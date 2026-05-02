from django.contrib import admin
from .models import Payment, SavedCard


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'method', 'status', 'amount', 'currency', 'created_at']
    list_filter = ['method', 'status', 'currency']
    search_fields = ['order__order_id', 'user__email', 'gateway_payment_id', 'gateway_order_id']
    readonly_fields = ['created_at', 'updated_at', 'gateway_response']


@admin.register(SavedCard)
class SavedCardAdmin(admin.ModelAdmin):
    list_display = ['user', 'brand', 'last4', 'expiry', 'is_default', 'gateway']
    list_filter = ['gateway', 'brand', 'is_default']
    search_fields = ['user__email', 'last4']
