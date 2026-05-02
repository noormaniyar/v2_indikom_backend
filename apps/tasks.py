"""
Celery tasks — async jobs triggered by views.

Usage (in views):
    from apps.tasks import send_order_email_task
    send_order_email_task.delay(order_id=order.id)
"""
from celery import shared_task


@shared_task(name='send_otp_sms')
def send_otp_sms_task(phone: str, otp_code: str):
    """
    Send OTP via SMS. Integrate your SMS provider here.
    Providers: MSG91, Twilio, Fast2SMS, etc.
    """
    # Example with MSG91:
    # import requests
    # requests.post('https://api.msg91.com/api/v5/otp', json={
    #     'mobile': phone, 'otp': otp_code, 'template_id': 'YOUR_TEMPLATE_ID',
    # }, headers={'authkey': 'YOUR_MSG91_KEY'})
    print(f"[SMS] Sending OTP {otp_code} to {phone}")


@shared_task(name='send_order_confirmation_email')
def send_order_email_task(order_id: int):
    from apps.orders.models import Order
    from apps.utils import send_order_confirmation_email
    try:
        order = Order.objects.select_related('user').get(id=order_id)
        send_order_confirmation_email(order.user, order)
    except Order.DoesNotExist:
        pass


@shared_task(name='send_supplier_approval_email')
def send_supplier_approval_task(supplier_id: int, approved: bool, reason: str = ''):
    from apps.accounts.models import SupplierProfile
    from apps.utils import send_supplier_approval_email
    try:
        profile = SupplierProfile.objects.select_related('user').get(id=supplier_id)
        send_supplier_approval_email(profile, approved, reason)
    except SupplierProfile.DoesNotExist:
        pass


@shared_task(name='create_order_notification')
def create_order_notification_task(user_id: int, order_id: str, event: str):
    from apps.accounts.models import User
    from apps.notifications.models import Notification, create_notification

    EVENT_MAP = {
        'placed': ('Order Placed 🛍️', f'Your order {order_id} has been placed successfully.', Notification.Type.ORDER_PLACED),
        'confirmed': ('Order Confirmed ✅', f'Order {order_id} is confirmed and being prepared.', Notification.Type.ORDER_CONFIRMED),
        'shipped': ('Order Shipped 🚚', f'Order {order_id} is on its way!', Notification.Type.ORDER_SHIPPED),
        'delivered': ('Order Delivered 📦', f'Order {order_id} has been delivered. Enjoy!', Notification.Type.ORDER_DELIVERED),
        'cancelled': ('Order Cancelled ❌', f'Order {order_id} has been cancelled.', Notification.Type.ORDER_CANCELLED),
    }

    try:
        user = User.objects.get(id=user_id)
        title, body, notif_type = EVENT_MAP.get(event, ('Update', f'Order {order_id} updated.', Notification.Type.GENERAL))
        create_notification(user, title, body, notif_type, data={'order_id': order_id})
    except User.DoesNotExist:
        pass


@shared_task(name='update_product_rating')
def update_product_rating_task(product_id: int):
    """Recalculate product average rating from all reviews."""
    from apps.products.models import Product, ProductReview
    from django.db.models import Avg
    try:
        product = Product.objects.get(id=product_id)
        agg = ProductReview.objects.filter(product=product, is_approved=True).aggregate(avg=Avg('rating'))
        product.rating = round(agg['avg'] or 0, 2)
        product.review_count = ProductReview.objects.filter(product=product, is_approved=True).count()
        product.save(update_fields=['rating', 'review_count'])
    except Product.DoesNotExist:
        pass


@shared_task(name='expire_unpaid_orders')
def expire_unpaid_orders_task():
    """Cancel orders that haven't been paid after 30 minutes (for online payment)."""
    from apps.orders.models import Order
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(minutes=30)
    stale = Order.objects.filter(
        status=Order.Status.PENDING,
        payment_status=Order.PaymentStatus.PENDING,
        created_at__lt=cutoff
    ).exclude(items__item_status=Order.Status.DELIVERED)

    count = stale.count()
    stale.update(status=Order.Status.CANCELLED, cancellation_reason='Auto-cancelled: payment timeout')
    print(f"[Celery] Expired {count} unpaid orders")
