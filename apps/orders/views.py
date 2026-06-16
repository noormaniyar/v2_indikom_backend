from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal

from .models import Order, OrderItem, OrderStatusHistory, Coupon, ReturnRequest
from .serializers import (
    OrderSerializer, PlaceOrderSerializer, CouponSerializer,
    ValidateCouponSerializer, ReturnRequestSerializer
)
from apps.accounts.models import Address
from apps.accounts.permissions import IsAdmin, IsModerator, IsApprovedSupplier
from apps.products.models import Cart, CartItem, Product
from apps.notifications.models import Notification
from apps.accounts.models import User
from apps.notifications.services import send_push_notification

class PlaceOrderView(APIView):
    """Place order from cart"""
    @transaction.atomic
    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        if not cart.items.exists():
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate address
        address = get_object_or_404(Address, id=data['address_id'], user=request.user)

        # Calculate totals
        subtotal = Decimal('0')
        items_data = []
        for item in cart.items.select_related('product', 'variant').all():
            if item.product.stock < item.quantity:
                return Response(
                    {'error': f'Insufficient stock for {item.product.name}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            unit_price = item.unit_price
            subtotal += unit_price * item.quantity
            items_data.append({
                'product': item.product,
                'variant': item.variant,
                'quantity': item.quantity,
                'unit_price': unit_price,
            })

        # Apply coupon
        discount_amount = Decimal('0')
        coupon_obj = None
        coupon_code = data.get('coupon_code', '')
        if coupon_code:
            try:
                coupon_obj = Coupon.objects.get(code=coupon_code)
                valid, msg = coupon_obj.is_valid()
                if not valid:
                    return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
                if subtotal < coupon_obj.minimum_order_amount:
                    return Response(
                        {'error': f'Minimum order amount is {coupon_obj.minimum_order_amount}.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                discount_amount = coupon_obj.calculate_discount(subtotal)
            except Coupon.DoesNotExist:
                return Response({'error': 'Invalid coupon code.'}, status=status.HTTP_400_BAD_REQUEST)

        shipping_charge = Decimal('0')  # free shipping logic here
        tax_rate = Decimal('0.08')  # 8% tax
        taxable_amount = subtotal - discount_amount
        tax_amount = round(taxable_amount * tax_rate, 2)
        total_amount = taxable_amount + tax_amount + shipping_charge

        # Create order
        order = Order.objects.create(
            user=request.user,
            shipping_address_snapshot={
                'full_name': address.full_name,
                'phone': str(address.phone),
                'line1': address.line1,
                'line2': address.line2,
                'city': address.city,
                'state': address.state,
                'country': address.country,
                'pincode': address.pincode,
            },
            subtotal=subtotal,
            shipping_charge=shipping_charge,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            coupon=coupon_obj,
            coupon_code=coupon_code,
            notes=data.get('notes', ''),
        )

        # Create order items & deduct stock
        for item_data in items_data:
            product = item_data['product']
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=item_data['variant'],
                supplier=product.supplier,
                product_name=product.name,
                variant_label=item_data['variant'].variant_label if item_data['variant'] else '',
                product_thumbnail=str(product.thumbnail) if product.thumbnail else '',
                sku=product.sku or '',
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
            )
            # Deduct stock
            product.stock -= item_data['quantity']
            product.save(update_fields=['stock'])

        # Use coupon
        if coupon_obj:
            coupon_obj.used_count += 1
            coupon_obj.save(update_fields=['used_count'])

        # Log status
        OrderStatusHistory.objects.create(
            order=order, status=Order.Status.PENDING,
            note='Order placed by customer.', created_by=request.user
        )

        # Clear cart
        cart.items.all().delete()

        # Create In-App Notification
        Notification.objects.create(
            user=request.user,
            title="Order Placed",
            message=f"Your order #{order.order_number if hasattr(order, 'order_number') else order.id} has been placed successfully.",
            notification_event="order_placed",
            notification_type="in_app",
            metadata={
                "order_id": order.id
            }
        )

        # Send Push Notification
        if request.user.onesignal_player_id:
            send_push_notification(
                player_id=request.user.onesignal_player_id,
                title="Order Placed",
                message="Your order has been placed successfully."
            )
        return Response({
            'message': 'Order placed successfully.',
            'order': OrderSerializer(order).data,
            'payment_required': data['payment_method'] != 'cod',
            'payment_method': data['payment_method'],
        }, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items', 'status_history')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), order_id=self.kwargs['order_id'])


class CancelOrderView(APIView):
    def post(self, request, order_id):
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        cancellable_statuses = [Order.Status.PENDING, Order.Status.CONFIRMED]
        if order.status not in cancellable_statuses:
            return Response(
                {'error': 'Order cannot be cancelled at this stage.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        reason = request.data.get('reason', '')
        order.status = Order.Status.CANCELLED
        order.cancellation_reason = reason
        order.save()
        OrderStatusHistory.objects.create(
            order=order, status=Order.Status.CANCELLED,
            note=f'Cancelled by customer. Reason: {reason}', created_by=request.user
        )
        # Restore stock
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock'])
        return Response({'message': 'Order cancelled successfully.'})


class ValidateCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ValidateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        amount = serializer.validated_data['order_amount']

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({'valid': False, 'error': 'Invalid coupon code.'}, status=status.HTTP_404_NOT_FOUND)

        valid, msg = coupon.is_valid()
        if not valid:
            return Response({'valid': False, 'error': msg})

        if amount < coupon.minimum_order_amount:
            return Response({'valid': False, 'error': f'Minimum order amount is {coupon.minimum_order_amount}.'})

        discount = coupon.calculate_discount(amount)
        return Response({
            'valid': True,
            'coupon': CouponSerializer(coupon).data,
            'discount_amount': discount,
            'final_amount': amount - discount,
        })


# ─── SUPPLIER ORDER VIEWS ─────────────────────────────────────────────────────

class SupplierOrderListView(generics.ListAPIView):
    """Supplier sees only their items across all orders"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]

    def get_queryset(self):
        supplier = self.request.user.supplier_profile
        order_ids = OrderItem.objects.filter(supplier=supplier).values_list('order_id', flat=True).distinct()
        return Order.objects.filter(id__in=order_ids).prefetch_related('items')


class SupplierUpdateItemStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]

    def patch(self, request, item_id):
        supplier = request.user.supplier_profile
        item = get_object_or_404(OrderItem, id=item_id, supplier=supplier)
        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Order.Status.choices]
        if new_status not in valid_statuses:
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
        item.item_status = new_status
        item.save()
        return Response({'message': f'Item status updated to {new_status}.'})


# ─── RETURN REQUESTS ──────────────────────────────────────────────────────────

class ReturnRequestView(generics.ListCreateAPIView):
    serializer_class = ReturnRequestSerializer

    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        order = get_object_or_404(Order, id=serializer.validated_data['order'].id, user=self.request.user)
        if order.status != Order.Status.DELIVERED:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Return can only be requested for delivered orders.')
        serializer.save(user=self.request.user)
        order.status = Order.Status.RETURN_REQUESTED
        order.save()


# ─── ADMIN ORDER VIEWS ────────────────────────────────────────────────────────

class AdminOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def get_queryset(self):
        qs = Order.objects.all().prefetch_related('items', 'status_history')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AdminOrderUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsModerator]

    def patch(self, request, order_id):
        order = get_object_or_404(Order, order_id=order_id)
        new_status = request.data.get('status')
        note = request.data.get('note', '')

        if new_status:
            order.status = new_status
            order.save()
            OrderStatusHistory.objects.create(
                order=order, status=new_status,
                note=note, created_by=request.user
            )

        return Response({'message': 'Order updated.', 'order': OrderSerializer(order).data})
