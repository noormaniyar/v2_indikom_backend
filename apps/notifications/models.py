from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_PLACED = 'order_placed', 'Order Placed'
        ORDER_CONFIRMED = 'order_confirmed', 'Order Confirmed'
        ORDER_SHIPPED = 'order_shipped', 'Order Shipped'
        ORDER_DELIVERED = 'order_delivered', 'Order Delivered'
        ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'
        PAYMENT_SUCCESS = 'payment_success', 'Payment Successful'
        PAYMENT_FAILED = 'payment_failed', 'Payment Failed'
        PRODUCT_APPROVED = 'product_approved', 'Product Approved'
        PRODUCT_REJECTED = 'product_rejected', 'Product Rejected'
        SUPPLIER_APPROVED = 'supplier_approved', 'Supplier Approved'
        RETURN_UPDATE = 'return_update', 'Return Update'
        PROMO = 'promo', 'Promotion'
        GENERAL = 'general', 'General'

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=30, choices=Type.choices, default=Type.GENERAL)
    data = models.JSONField(blank=True, null=True)  # Extra payload (order_id, product_id, etc.)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}: {self.title}"


# ─── SERIALIZERS, VIEWS, URLS ─────────────────────────────────────────────────
from rest_framework import generics, serializers, permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'notification_type', 'data', 'is_read', 'created_at']


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkReadView(APIView):
    def post(self, request, pk=None):
        if pk:
            Notification.objects.filter(user=request.user, pk=pk).update(is_read=True)
        else:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Marked as read.'})


class UnreadCountView(APIView):
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


# Helper function - call this from other views to create notifications
def create_notification(user, title, body, notification_type=Notification.Type.GENERAL, data=None):
    Notification.objects.create(
        user=user, title=title, body=body,
        notification_type=notification_type, data=data
    )


from django.urls import path

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', UnreadCountView.as_view(), name='notification-unread'),
    path('mark-read/', MarkReadView.as_view(), name='notification-mark-all-read'),
    path('<int:pk>/mark-read/', MarkReadView.as_view(), name='notification-mark-read'),
]
