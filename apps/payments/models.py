"""
Payments App - models.py, serializers.py, views.py, urls.py all-in-one.
Split into separate files if preferred.
"""

# ─── models.py ────────────────────────────────────────────────────────────────
from django.db import models


class Payment(models.Model):
    class Method(models.TextChoices):
        RAZORPAY = 'razorpay', 'Razorpay'
        STRIPE = 'stripe', 'Stripe'
        COD = 'cod', 'Cash on Delivery'
        UPI = 'upi', 'UPI'
        WALLET = 'wallet', 'Wallet'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')

    # Gateway-specific IDs
    gateway_order_id = models.CharField(max_length=200, blank=True)
    gateway_payment_id = models.CharField(max_length=200, blank=True)
    gateway_signature = models.CharField(max_length=500, blank=True)
    gateway_response = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order {self.order.order_id} - {self.status}"


class SavedCard(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='saved_cards')
    gateway = models.CharField(max_length=20)
    token = models.CharField(max_length=500)  # gateway token (NOT actual card data)
    last4 = models.CharField(max_length=4)
    brand = models.CharField(max_length=20, blank=True)
    expiry = models.CharField(max_length=10, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} ****{self.last4} ({self.user.email})"
