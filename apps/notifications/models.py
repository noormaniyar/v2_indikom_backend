from django.db import models
from django.conf import settings

class Notification(models.Model):

    NOTIFICATION_EVENTS = (
        ('order_placed' , 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('payment_success', 'Payment Successful'),
        ('payment_failed', 'Payment Failed'),
        ('product_approved', 'Product Approved'),
        ('product_rejected', 'Product Rejected'),
        ('supplier_approved', 'Supplier Approved'),
        ('return_update', 'Return Update'),
        ('promo', 'Promotion'),
        ('general', 'General')
    )
    NOTIFICATION_TYPES = (
        ('push' , 'Push'),
        ('in_app', 'In pp'),
        ('email', 'Email'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    notification_event = models.CharField(
        max_length=20,
        choices=NOTIFICATION_EVENTS,
        default='general'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='push'
    )

    is_read = models.BooleanField(default=False)

    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Store order_id, chat_id, supplier_id etc."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} - {self.title}"
