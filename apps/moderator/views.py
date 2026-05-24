from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from apps.accounts.permissions import IsModerator, IsAdmin
from apps.accounts.models import SupplierProfile, ModeratorProfile, User
from apps.accounts.serializers import SupplierProfileSerializer, UserSerializer
from apps.products.models import Product
from apps.products.serializers import ProductDetailSerializer
from apps.orders.models import Order


# ─── SERIALIZERS ──────────────────────────────────────────────────────────────

class ApproveSupplierSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject', 'suspend'])
    reason = serializers.CharField(required=False, allow_blank=True)


class ApproveProductSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)


# ─── VIEWS ────────────────────────────────────────────────────────────────────

class DashboardView(APIView):
    """Admin/Moderator dashboard stats"""
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get(self, request):
        now = timezone.now()
        last_30 = now - timedelta(days=30)

        return Response({
            'users': {
                'total': User.objects.count(),
                'customers': User.objects.filter(role=User.Role.CUSTOMER).count(),
                'suppliers': User.objects.filter(role=User.Role.SUPPLIER).count(),
                'new_this_month': User.objects.filter(created_at__gte=last_30).count(),
            },
            'products': {
                'total': Product.objects.count(),
                'pending': Product.objects.filter(moderation_status=Product.ModerationStatus.PENDING).count(),
                'approved': Product.objects.filter(moderation_status=Product.ModerationStatus.APPROVED).count(),
                'rejected': Product.objects.filter(moderation_status=Product.ModerationStatus.REJECTED).count(),
            },
            'orders': {
                'total': Order.objects.count(),
                'pending': Order.objects.filter(status=Order.Status.PENDING).count(),
                'delivered': Order.objects.filter(status=Order.Status.DELIVERED).count(),
                'revenue_total': Order.objects.filter(payment_status=Order.PaymentStatus.PAID).aggregate(
                    total=Sum('total_amount'))['total'] or 0,
                'revenue_this_month': Order.objects.filter(
                    payment_status=Order.PaymentStatus.PAID, created_at__gte=last_30
                ).aggregate(total=Sum('total_amount'))['total'] or 0,
            },
            'suppliers': {
                'total': SupplierProfile.objects.count(),
                'pending': SupplierProfile.objects.filter(status=SupplierProfile.Status.PENDING).count(),
                'approved': SupplierProfile.objects.filter(status=SupplierProfile.Status.APPROVED).count(),
            }
        })


# ─── SUPPLIER MODERATION ──────────────────────────────────────────────────────

class SupplierListView(generics.ListAPIView):
    serializer_class = SupplierProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get_queryset(self):
        return SupplierProfile.objects.all()

class PendingSupplierListView(generics.ListAPIView):
    serializer_class = SupplierProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'pending')
        return SupplierProfile.objects.filter(status=status_filter).select_related('user')


class ModerateSupplierView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def post(self, request, pk):
        supplier = get_object_or_404(SupplierProfile, pk=pk)
        serializer = ApproveSupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')

        status_map = {
            'approve': SupplierProfile.Status.APPROVED,
            'reject': SupplierProfile.Status.REJECTED,
            'suspend': SupplierProfile.Status.SUSPENDED,
        }
        supplier.status = status_map[action]
        if action in ['reject', 'suspend']:
            supplier.rejection_reason = reason
        supplier.save()

        # TODO: send email notification to supplier
        return Response({'message': f'Supplier {action}d successfully.', 'status': supplier.status})


# ─── PRODUCT MODERATION ───────────────────────────────────────────────────────

class ProductListView(generics.ListAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get_queryset(self):
        return Product.objects.all()


class PendingProductListView(generics.ListAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'pending')
        return Product.objects.filter(moderation_status=status_filter).select_related('supplier', 'category')


class ModerateProductView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ApproveProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')

        if action == 'approve':
            product.moderation_status = Product.ModerationStatus.APPROVED
            product.rejection_reason = ''
        else:
            product.moderation_status = Product.ModerationStatus.REJECTED
            product.rejection_reason = reason
        product.save()

        return Response({'message': f'Product {action}d.', 'moderation_status': product.moderation_status})


class FeatureProductView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_featured = not product.is_featured
        product.save()
        return Response({'is_featured': product.is_featured})


# ─── USER MANAGEMENT ──────────────────────────────────────────────────────────

class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get_queryset(self):
        qs = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

class SetRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.role = self.request.data.get('role')
        print(user.role, '---user.role------')
        user.save()
        if user.role == 'supplier':
            SupplierProfile.objects.create(
                user=user,
                business_name=user.full_name or user.email,
                status = 'approved'
            )
        if user.role == 'moderator':
            ModeratorProfile.objects.create(
                user=user,
                status = 'approved'
            )
        return Response({'role': user.role})

class UserToggleActiveView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        return Response({'is_active': user.is_active})

