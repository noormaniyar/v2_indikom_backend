from rest_framework.permissions import BasePermission
from .models import User


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.CUSTOMER


class IsSupplier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.SUPPLIER


class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [User.Role.MODERATOR, User.Role.ADMIN]


class IsDeliveryAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.DELIVERY_AGENT


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN


class IsApprovedSupplier(BasePermission):
    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.role == User.Role.SUPPLIER):
            return False
        try:
            return request.user.supplier_profile.status == 'approved'
        except Exception:
            return False


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True
        return obj.user == request.user
