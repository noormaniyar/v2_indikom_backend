from apps.notifications.services import create_notification
from apps.orders.models import Order


def create_order(*, customer, items, address):
    order = Order.objects.create(
        customer=customer
    )
    create_notification(
        user=customer,
        title="Order Placed",
        message="Your order has been placed successfully.",
        notification_event="order_placed",
        metadata={
            "order_id": order.id
        }
    )
    return order
