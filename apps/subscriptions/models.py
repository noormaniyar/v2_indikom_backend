from django.db import models


class SubscriptionPlan(models.Model):
    class PlanType(models.TextChoices):
        SUPPLIER_BASIC = 'supplier_basic', 'Supplier Basic'
        SUPPLIER_PRO = 'supplier_pro', 'Supplier Pro'
        SUPPLIER_ENTERPRISE = 'supplier_enterprise', 'Supplier Enterprise'

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=50, choices=PlanType.choices, unique=True)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    max_products = models.IntegerField(default=50, help_text='0 = unlimited')
    commission_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SupplierSubscription(models.Model):
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'
        TRIAL = 'trial', 'Trial'

    supplier = models.ForeignKey('accounts.SupplierProfile', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    billing_cycle = models.CharField(max_length=10, choices=BillingCycle.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_ref = models.CharField(max_length=200, blank=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.supplier.business_name} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        from django.utils import timezone
        return self.status == self.Status.ACTIVE and self.end_date >= timezone.now().date()
