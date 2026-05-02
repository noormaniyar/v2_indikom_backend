from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import SubscriptionPlan, SupplierSubscription
from apps.accounts.permissions import IsSupplier, IsAdmin


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class SupplierSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = SupplierSubscription
        fields = '__all__'
        read_only_fields = ['supplier', 'created_at']


class PlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class SupplierSubscriptionView(generics.ListAPIView):
    serializer_class = SupplierSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSupplier]

    def get_queryset(self):
        return SupplierSubscription.objects.filter(
            supplier=self.request.user.supplier_profile
        )


class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSupplier]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        from datetime import date, timedelta
        start = date.today()
        end = start + timedelta(days=365 if billing_cycle == 'yearly' else 30)
        amount = plan.price_yearly if billing_cycle == 'yearly' else plan.price_monthly

        sub = SupplierSubscription.objects.create(
            supplier=request.user.supplier_profile,
            plan=plan, billing_cycle=billing_cycle,
            start_date=start, end_date=end, amount_paid=amount,
        )

        # Update supplier commission based on plan
        supplier = request.user.supplier_profile
        supplier.commission_rate = max(5, 10 - plan.commission_discount)
        supplier.save()

        return Response({
            'message': 'Subscription activated.',
            'subscription': SupplierSubscriptionSerializer(sub).data
        })


from django.urls import path

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='subscription-plans'),
    path('my/', SupplierSubscriptionView.as_view(), name='my-subscriptions'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
]
