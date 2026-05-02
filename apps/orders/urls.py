from django.urls import path
from . import views

urlpatterns = [
    # Customer
    path('place/', views.PlaceOrderView.as_view(), name='place-order'),
    path('', views.OrderListView.as_view(), name='order-list'),
    path('<str:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<str:order_id>/cancel/', views.CancelOrderView.as_view(), name='order-cancel'),

    # Coupons
    path('coupons/validate/', views.ValidateCouponView.as_view(), name='coupon-validate'),

    # Returns
    path('returns/', views.ReturnRequestView.as_view(), name='return-list'),

    # Supplier
    path('supplier/orders/', views.SupplierOrderListView.as_view(), name='supplier-order-list'),
    path('supplier/items/<int:item_id>/status/', views.SupplierUpdateItemStatusView.as_view(), name='supplier-item-status'),

    # Admin/Moderator
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<str:order_id>/', views.AdminOrderUpdateView.as_view(), name='admin-order-update'),
]
