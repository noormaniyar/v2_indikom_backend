from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, Address, SupplierProfile, ModeratorProfile, DeliveryAgentProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone', 'email', 'full_name', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'profile_picture', 'preferred_language')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(ModeratorProfile)
class ModeratorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at']
    list_filter = ['status']
@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'status', 'commission_rate', 'rating', 'created_at']
    list_filter = ['status']
    search_fields = ['business_name', 'user__email', 'gstin']
    actions = ['approve_suppliers', 'reject_suppliers', 'suspend_suppliers']

    def approve_suppliers(self, request, queryset):
        queryset.update(status=SupplierProfile.Status.APPROVED)
    approve_suppliers.short_description = 'Approve selected suppliers'

    def reject_suppliers(self, request, queryset):
        queryset.update(status=SupplierProfile.Status.REJECTED)
    reject_suppliers.short_description = 'Reject selected suppliers'

    def suspend_suppliers(self, request, queryset):
        queryset.update(status=SupplierProfile.Status.SUSPENDED)
    suspend_suppliers.short_description = 'Suspend selected suppliers'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'state', 'is_default']
    list_filter = ['label', 'is_default', 'country']
    search_fields = ['user__email', 'full_name', 'city', 'pincode']


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'purpose', 'is_used', 'expires_at']
    list_filter = ['purpose', 'is_used']
    search_fields = ['user__email', 'code']


@admin.register(DeliveryAgentProfile)
class DeliveryAgentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'vehicle_type', 'vehicle_number', 'status', 'rating', 'total_deliveries']
    list_filter = ['status', 'vehicle_type']
    search_fields = ['user__email', 'vehicle_number', 'license_number']
