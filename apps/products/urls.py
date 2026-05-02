from django.urls import path
from . import views

urlpatterns = [
    # ── Categories ────────────────────────────────────────────────────────────
    path('categories/tree/', views.CategoryTreeView.as_view(), name='category-tree'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('subcategories/', views.SubCategoryListView.as_view(), name='subcategory-list'),
    path('subcategories/<slug:slug>/', views.SubCategoryDetailView.as_view(), name='subcategory-detail'),

    # ── Attributes & Specs ────────────────────────────────────────────────────
    path('attributes/', views.AttributeDefinitionListView.as_view(), name='attribute-list'),
    path('spec-templates/', views.SpecificationTemplateView.as_view(), name='spec-template-list'),

    # ── Products (public) ─────────────────────────────────────────────────────
    path('', views.ProductListView.as_view(), name='product-list'),
    path('featured/', views.FeaturedProductsView.as_view(), name='featured-products'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),

    # ── Product Reviews (public read, auth write) ─────────────────────────────
    path('<slug:slug>/reviews/', views.ProductReviewListCreateView.as_view(), name='product-reviews'),

    # ── Supplier: product management ──────────────────────────────────────────
    path('supplier/products/', views.SupplierProductListCreateView.as_view(), name='supplier-product-list'),
    path('supplier/products/<int:pk>/', views.SupplierProductDetailView.as_view(), name='supplier-product-detail'),

    # ── Product Images ────────────────────────────────────────────────────────
    path('supplier/products/<int:product_id>/images/', views.ProductImageUploadView.as_view(), name='product-image-upload'),
    path('supplier/images/<int:pk>/', views.ProductImageDeleteView.as_view(), name='product-image-delete'),

    # ── Product Variants ──────────────────────────────────────────────────────
    path('supplier/products/<int:product_id>/variants/', views.ProductVariantListCreateView.as_view(), name='product-variant-list'),
    path('supplier/variants/<int:pk>/', views.ProductVariantDetailView.as_view(), name='product-variant-detail'),

    # ── Wishlist ──────────────────────────────────────────────────────────────
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:pk>/', views.WishlistDeleteView.as_view(), name='wishlist-delete'),
    path('wishlist/toggle/<int:product_id>/', views.WishlistToggleView.as_view(), name='wishlist-toggle'),

    # ── Cart ──────────────────────────────────────────────────────────────────
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.CartItemAddView.as_view(), name='cart-add'),
    path('cart/items/<int:pk>/', views.CartItemUpdateView.as_view(), name='cart-item-update'),
    path('cart/clear/', views.CartClearView.as_view(), name='cart-clear'),
]
