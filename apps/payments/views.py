from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.conf import settings

from .models import Payment, SavedCard
from apps.orders.models import Order


# ─── SERIALIZERS ──────────────────────────────────────────────────────────────

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'method', 'status', 'amount', 'currency',
            'gateway_order_id', 'gateway_payment_id', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    method = serializers.ChoiceField(choices=Payment.Method.choices)


class VerifyRazorpaySerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class VerifyStripeSerializer(serializers.Serializer):
    payment_intent_id = serializers.CharField()


# ─── VIEWS ────────────────────────────────────────────────────────────────────

class InitiatePaymentView(APIView):
    """Creates gateway order/intent and returns client secret / order_id"""
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order = get_object_or_404(Order, order_id=data['order_id'], user=request.user)

        if order.payment_status == Order.PaymentStatus.PAID:
            return Response({'error': 'Order is already paid.'}, status=status.HTTP_400_BAD_REQUEST)

        method = data['method']
        amount = int(order.total_amount * 100)  # paise for Razorpay, cents for Stripe

        response_data = {}

        if method == Payment.Method.RAZORPAY:
            try:
                import razorpay
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                rz_order = client.order.create({
                    'amount': amount,
                    'currency': 'INR',
                    'receipt': order.order_id,
                })
                payment = Payment.objects.update_or_create(
                    order=order,
                    defaults={
                        'user': request.user,
                        'method': method,
                        'amount': order.total_amount,
                        'gateway_order_id': rz_order['id'],
                    }
                )[0]
                response_data = {
                    'gateway': 'razorpay',
                    'key_id': settings.RAZORPAY_KEY_ID,
                    'razorpay_order_id': rz_order['id'],
                    'amount': amount,
                    'currency': 'INR',
                }
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif method == Payment.Method.STRIPE:
            try:
                import stripe
                stripe.api_key = settings.STRIPE_SECRET_KEY
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency='usd',
                    metadata={'order_id': order.order_id},
                )
                payment = Payment.objects.update_or_create(
                    order=order,
                    defaults={
                        'user': request.user,
                        'method': method,
                        'amount': order.total_amount,
                        'gateway_order_id': intent['id'],
                    }
                )[0]
                response_data = {
                    'gateway': 'stripe',
                    'client_secret': intent['client_secret'],
                    'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
                }
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif method == Payment.Method.COD:
            payment, _ = Payment.objects.update_or_create(
                order=order,
                defaults={
                    'user': request.user,
                    'method': method,
                    'amount': order.total_amount,
                    'status': Payment.Status.PENDING,
                }
            )
            order.status = Order.Status.CONFIRMED
            order.payment_status = Order.PaymentStatus.PENDING
            order.save()
            response_data = {'gateway': 'cod', 'message': 'Cash on delivery confirmed.'}

        return Response({**response_data, 'payment_id': payment.id})


class VerifyRazorpayView(APIView):
    def post(self, request):
        serializer = VerifyRazorpaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            import razorpay
            import hmac, hashlib
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}".encode(),
                hashlib.sha256
            ).hexdigest()

            if generated_signature != data['razorpay_signature']:
                return Response({'error': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

            payment = get_object_or_404(Payment, gateway_order_id=data['razorpay_order_id'])
            payment.gateway_payment_id = data['razorpay_payment_id']
            payment.gateway_signature = data['razorpay_signature']
            payment.status = Payment.Status.SUCCESS
            payment.save()

            # Update order
            payment.order.payment_status = Order.PaymentStatus.PAID
            payment.order.status = Order.Status.CONFIRMED
            payment.order.save()

            return Response({'message': 'Payment verified successfully.', 'order_id': payment.order.order_id})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


# ─── URLS ─────────────────────────────────────────────────────────────────────
from django.urls import path

urlpatterns = [
    path('initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('verify/razorpay/', VerifyRazorpayView.as_view(), name='payment-verify-razorpay'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
]
