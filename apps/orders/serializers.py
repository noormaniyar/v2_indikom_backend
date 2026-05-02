from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, Coupon, ReturnRequest
from apps.products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'product_name', 'variant_label',
            'product_thumbnail', 'sku', 'quantity', 'unit_price', 'subtotal', 'item_status',
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'note', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'status', 'payment_status',
            'shipping_address_snapshot', 'subtotal', 'shipping_charge',
            'tax_amount', 'discount_amount', 'total_amount',
            'coupon_code', 'notes', 'estimated_delivery', 'delivered_at',
            'items', 'status_history', 'created_at', 'updated_at',
        ]
        read_only_fields = ['order_id', 'status', 'payment_status', 'subtotal', 'total_amount']


class PlaceOrderSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=['razorpay', 'stripe', 'cod', 'upi'])


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'description', 'discount_type', 'discount_value',
                  'minimum_order_amount', 'max_discount_amount', 'valid_until']


class ValidateCouponSerializer(serializers.Serializer):
    code = serializers.CharField()
    order_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = ['id', 'order', 'order_item', 'reason', 'description', 'status',
                  'rejection_reason', 'refund_amount', 'created_at']
        read_only_fields = ['id', 'status', 'rejection_reason', 'refund_amount', 'created_at']
