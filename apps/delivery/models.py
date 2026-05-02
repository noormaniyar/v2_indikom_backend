from django.db import models


class Shipment(models.Model):
    class Status(models.TextChoices):
        CREATED = 'created', 'Created'
        PICKED_UP = 'picked_up', 'Picked Up from Supplier'
        IN_TRANSIT = 'in_transit', 'In Transit'
        OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
        DELIVERED = 'delivered', 'Delivered'
        FAILED_ATTEMPT = 'failed_attempt', 'Failed Delivery Attempt'
        RETURNED = 'returned', 'Returned to Supplier'

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='shipment')
    delivery_agent = models.ForeignKey(
        'accounts.DeliveryAgentProfile', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='shipments'
    )
    tracking_id = models.CharField(max_length=100, unique=True, blank=True)
    courier_partner = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CREATED)
    current_location = models.CharField(max_length=255, blank=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivery_otp = models.CharField(max_length=6, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            import uuid
            self.tracking_id = f"TRK{str(uuid.uuid4().int)[:10]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipment {self.tracking_id} - {self.status}"


class ShipmentTracking(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_events')
    status = models.CharField(max_length=30, choices=Shipment.Status.choices)
    location = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=500)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shipment.tracking_id}: {self.status} at {self.location}"
