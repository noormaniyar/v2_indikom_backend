from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import (
    Category, SubCategory, SpecificationTemplate, AttributeDefinition, AttributeValue,
    Product, ProductName, ProductImage, ProductVariant, VariantAttribute, ProductSpecification,
    Wishlist, ProductReview, ReviewImage, Cart, CartItem
)


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'sort_order', 'full_path']
    list_filter = ['is_active', 'level']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    mptt_level_indent = 20


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'sort_order']
    list_filter = ['is_active', 'category']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'category', 'price', 'discount_price', 'stock', 'moderation_status', 'is_active', 'is_featured']
    list_filter = ['moderation_status', 'is_active', 'is_featured', 'category', 'has_ar']
    search_fields = ['name', 'brand', 'sku', 'tags']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline, ProductSpecificationInline]
    actions = ['approve_products', 'reject_products', 'feature_products']

    def approve_products(self, request, queryset):
        queryset.update(moderation_status=Product.ModerationStatus.APPROVED)
    approve_products.short_description = 'Approve selected products'

    def reject_products(self, request, queryset):
        queryset.update(moderation_status=Product.ModerationStatus.REJECTED)
    reject_products.short_description = 'Reject selected products'

    def feature_products(self, request, queryset):
        queryset.update(is_featured=True)
    feature_products.short_description = 'Mark as Featured'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'sku', 'price', 'discount_price', 'stock', 'is_active']
    list_filter = ['is_active']
    search_fields = ['sku', 'product__name']


@admin.register(AttributeDefinition)
class AttributeDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_global']
    list_filter = ['is_global', 'category']


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'display_value', 'sort_order']
    list_filter = ['attribute']
    search_fields = ['value']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_verified_purchase', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_verified_purchase']
    search_fields = ['product__name', 'user__email', 'title']
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = 'Approve selected reviews'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'total', 'updated_at']
    search_fields = ['user__email']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'added_at']


admin.site.register(ProductName)

