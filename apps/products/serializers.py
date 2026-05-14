from rest_framework import serializers
from .models import (
    Category, SubCategory, SpecificationTemplate, AttributeDefinition, AttributeValue,
    Product, ProductImage, ProductVariant, VariantAttribute, ProductSpecification,
    Wishlist, ProductReview, ReviewImage, Cart, CartItem
)


# ─── CATEGORY ─────────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    full_path = serializers.ReadOnlyField()
    level = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ['id', 'parent', 'name', 'slug', 'description', 'is_active',
                  'thumbnail', 'icon', 'sort_order', 'full_path', 'level', 'children']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class CategoryFlatSerializer(serializers.ModelSerializer):
    full_path = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ['id', 'parent', 'name', 'slug', 'thumbnail', 'icon', 'full_path', 'is_active', 'sort_order']


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'category', 'name', 'slug', 'description', 'is_active', 'thumbnail', 'sort_order']


# ─── SPECIFICATIONS & ATTRIBUTES ───────────────────────────────────────────────

class SpecificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationTemplate
        fields = ['id', 'category', 'key', 'unit', 'is_filterable', 'sort_order']


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = ['id', 'value', 'display_value', 'sort_order']


class AttributeDefinitionSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = AttributeDefinition
        fields = ['id', 'category', 'name', 'is_global', 'sort_order', 'values']


# ─── PRODUCT IMAGES ───────────────────────────────────────────────────────────

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'sort_order']


# ─── VARIANT ATTRIBUTE ────────────────────────────────────────────────────────

class VariantAttributeSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    value_display = serializers.CharField(source='value.value', read_only=True)

    class Meta:
        model = VariantAttribute
        fields = ['id', 'attribute', 'attribute_name', 'value', 'value_display']


class VariantAttributeWriteSerializer(serializers.Serializer):
    attribute_id = serializers.IntegerField()
    value_id = serializers.IntegerField()


# ─── PRODUCT VARIANT ──────────────────────────────────────────────────────────

class ProductVariantSerializer(serializers.ModelSerializer):
    variant_attributes = VariantAttributeSerializer(many=True, read_only=True)
    effective_price = serializers.ReadOnlyField()
    variant_label = serializers.ReadOnlyField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'price', 'discount_price', 'effective_price',
            'stock', 'is_active', 'thumbnail', 'weight',
            'variant_attributes', 'variant_label',
        ]


class ProductVariantWriteSerializer(serializers.ModelSerializer):
    attributes = VariantAttributeWriteSerializer(many=True, write_only=True)

    class Meta:
        model = ProductVariant
        fields = ['sku', 'price', 'discount_price', 'stock', 'is_active', 'thumbnail', 'weight', 'attributes']

    def create(self, validated_data):
        attributes_data = validated_data.pop('attributes', [])
        variant = ProductVariant.objects.create(**validated_data)
        for attr_data in attributes_data:
            VariantAttribute.objects.create(
                variant=variant,
                attribute_id=attr_data['attribute_id'],
                value_id=attr_data['value_id']
            )
        return variant

    def update(self, instance, validated_data):
        attributes_data = validated_data.pop('attributes', [])
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if attributes_data:
            instance.variant_attributes.all().delete()
            for attr_data in attributes_data:
                VariantAttribute.objects.create(
                    variant=instance,
                    attribute_id=attr_data['attribute_id'],
                    value_id=attr_data['value_id']
                )
        return instance


# ─── PRODUCT SPECIFICATION ────────────────────────────────────────────────────

class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'key', 'value', 'unit', 'sort_order']


# ─── PRODUCT ─────────────────────────────────────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views / search results"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    sub_category_name = serializers.CharField(source='sub_category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.business_name', read_only=True)
    effective_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'category', 'category_name',
            'sub_category', 'sub_category_name', 'supplier_name', 'supplier', 
            'description', 'weight', 'dimensions', 'tags', 'is_best_selling',
            'price', 'discount_price', 'effective_price', 'discount_percentage',
            'thumbnail', 'rating', 'review_count', 'stock', 'is_featured',
            'is_daily_use_item', 'is_top_deal',
            'has_ar', 'is_active', 'created_at',
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for product detail page"""
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_path = serializers.CharField(source='category.full_path', read_only=True)
    sub_category_name = serializers.CharField(source='sub_category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.business_name', read_only=True)
    supplier_id = serializers.IntegerField(source='supplier.id', read_only=True)
    effective_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_wishlisted = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'sku', 'description',
            'category', 'category_name', 'category_path',
            'sub_category', 'sub_category_name',
            'supplier_id', 'supplier_name',
            'price', 'discount_price', 'effective_price', 'discount_percentage',
            'stock', 'weight', 'dimensions', 'is_active', 'is_featured', 'is_daily_use_item', 'is_top_deal',
            'moderation_status', 'rating', 'review_count',
            'thumbnail', 'file', 'ar_file', 'has_ar', 'tags',
            'meta_title', 'meta_description',
            'images', 'variants', 'specifications',
            'is_wishlisted', 'created_at', 'updated_at',
        ]

    def get_is_wishlisted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, product=obj).exists()
        return False


class ProductWriteSerializer(serializers.ModelSerializer):
    """For supplier product upload form"""
    specifications = ProductSpecificationSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'name', 'category', 'sub_category', 'brand', 'sku', 'description',
            'price', 'discount_price', 'stock', 'weight', 'dimensions',
            'thumbnail', 'file', 'ar_file', 'tags',
            'meta_title', 'meta_description', 'specifications',
        ]

    def create(self, validated_data):
        specifications_data = validated_data.pop('specifications', [])
        product = Product.objects.create(**validated_data)
        for spec in specifications_data:
            ProductSpecification.objects.create(product=product, **spec)
        return product

    def update(self, instance, validated_data):
        specifications_data = validated_data.pop('specifications', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if specifications_data is not None:
            instance.specifications.all().delete()
            for spec in specifications_data:
                ProductSpecification.objects.create(product=instance, **spec)
        return instance


# ─── WISHLIST ─────────────────────────────────────────────────────────────────

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source='product'
    )

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_id', 'variant', 'added_at']
        read_only_fields = ['id', 'added_at']


# ─── REVIEWS ─────────────────────────────────────────────────────────────────

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'user_name', 'rating', 'title', 'body',
            'is_verified_purchase', 'helpful_count', 'images', 'created_at',
        ]
        read_only_fields = ['id', 'user_name', 'is_verified_purchase', 'helpful_count', 'created_at']


# ─── CART ─────────────────────────────────────────────────────────────────────

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source='product'
    )
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), write_only=True, source='variant', required=False, allow_null=True
    )
    subtotal = serializers.ReadOnlyField()
    unit_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'variant', 'variant_id', 'quantity', 'unit_price', 'subtotal', 'added_at']
        read_only_fields = ['id', 'subtotal', 'unit_price', 'added_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'item_count', 'updated_at']
