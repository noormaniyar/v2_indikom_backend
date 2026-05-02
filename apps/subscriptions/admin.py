from django.contrib import admin
from .models import SubscriptionPlan, SupplierSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_monthly', 'price_yearly', 'max_products', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'plan_type']


@admin.register(SupplierSubscription)
class SupplierSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'plan', 'status', 'billing_cycle', 'start_date', 'end_date', 'amount_paid']
    list_filter = ['status', 'billing_cycle', 'plan']
    search_fields = ['supplier__business_name', 'supplier__user__email']
    readonly_fields = ['created_at']
