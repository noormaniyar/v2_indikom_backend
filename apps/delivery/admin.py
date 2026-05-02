from django.contrib import admin
from .models import Shipment, ShipmentTracking


class ShipmentTrackingInline(admin.TabularInline):
    model = ShipmentTracking
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['tracking_id', 'order', 'delivery_agent', 'status', 'estimated_delivery', 'delivered_at']
    list_filter = ['status', 'courier_partner']
    search_fields = ['tracking_id', 'order__order_id', 'delivery_agent__user__email']
    readonly_fields = ['tracking_id', 'created_at', 'updated_at']
    inlines = [ShipmentTrackingInline]


@admin.register(ShipmentTracking)
class ShipmentTrackingAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'status', 'location', 'created_at']
    list_filter = ['status']
    search_fields = ['shipment__tracking_id']
