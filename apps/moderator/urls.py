# from .views import urlpatterns
from django.urls import path
from . import views


# ─── URLS ─────────────────────────────────────────────────────────────────────
from django.urls import path

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='moderator-dashboard'),

    # Supplier Moderation
    path('suppliers/', views.SupplierListView.as_view(), name='supplier-list'),
    path('pending_suppliers/', views.PendingSupplierListView.as_view(), name='mod-supplier-list'),
    path('suppliers/<int:pk>/moderate/', views.ModerateSupplierView.as_view(), name='mod-supplier-action'),

    # Product Moderation
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('pending_products/', views.PendingProductListView.as_view(), name='mod-product-list'),
    path('products/<int:pk>/moderate/', views.ModerateProductView.as_view(), name='mod-product-action'),
    path('products/<int:pk>/feature/', views.FeatureProductView.as_view(), name='mod-product-feature'),

    # User Management
    path('users/', views.UserListView.as_view(), name='mod-user-list'),
    path('users/<int:pk>/set-role/', views.SetRoleView.as_view(), name='set-role'),
    path('users/<int:pk>/toggle-active/', views.UserToggleActiveView.as_view(), name='mod-user-toggle'),
]
