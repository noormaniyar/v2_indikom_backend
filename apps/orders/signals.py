"""
apps/orders/signals.py
Auto-fire Celery tasks on order save events.
Connect in orders/apps.py ready() method.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


#@receiver(post_save, sender='orders.Order')
def order_status_changed(sender, instance, created, **kwargs):
    from apps.tasks import create_order_notification_task, send_order_email_task

    if created:
        # New order placed
        create_order_notification_task.delay(
            user_id=instance.user_id,
            order_id=instance.order_id,
            event='placed'
        )
        send_order_email_task.delay(order_id=instance.id)
    else:
        # Status change notification
        event_map = {
            'confirmed': 'confirmed',
            'shipped': 'shipped',
            'delivered': 'delivered',
            'cancelled': 'cancelled',
        }
        event = event_map.get(instance.status)
        if event and instance.user_id:
            create_order_notification_task.delay(
                user_id=instance.user_id,
                order_id=instance.order_id,
                event=event
            )
