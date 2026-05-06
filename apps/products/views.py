from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models

from .models import (
    Category, SubCategory, AttributeDefinition, SpecificationTemplate,
    Product, ProductImage, ProductVariant, ProductSpecification,
    Wishlist, ProductReview, ReviewImage, Cart, CartItem
)
from .serializers import (
    CategorySerializer, CategoryFlatSerializer, SubCategorySerializer,
    AttributeDefinitionSerializer, SpecificationTemplateSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductWriteSerializer,
    ProductImageSerializer, ProductVariantSerializer, ProductVariantWriteSerializer,
    ProductSpecificationSerializer, WishlistSerializer,
    ProductReviewSerializer, CartSerializer, CartItemSerializer
)
from .filters import ProductFilter
from apps.accounts.permissions import IsApprovedSupplier, IsModerator, IsAdmin


# ─── CATEGORY VIEWS ───────────────────────────────────────────────────────────

class CategoryTreeView(APIView):
    """Returns full category tree (root categories with nested children)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        root_categories = Category.objects.filter(parent=None, is_active=True)
        serializer = CategorySerializer(root_categories, many=True)
        return Response(serializer.data)


class CategoryListView(generics.ListCreateAPIView):
    """Flat list of all categories with optional filters"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = CategoryFlatSerializer
    filter_backends = [SearchFilter]
    search_fields = ['name', 'slug']

    def get_queryset(self):
        qs = Category.objects.all()
        parent = self.request.query_params.get('parent')
        level = self.request.query_params.get('level')
        if parent == 'null':
            qs = qs.filter(parent=None)
        elif parent:
            qs = qs.filter(parent__id=parent)
        if level:
            qs = qs.filter(level=level)
        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CategorySerializer
        return CategoryFlatSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class SubCategoryListView(generics.ListCreateAPIView):
    serializer_class = SubCategorySerializer

    def get_queryset(self):
        qs = SubCategory.objects.all()
        cat = self.request.query_params.get('category')
        if cat:
            qs = qs.filter(category__slug=cat)
        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class SubCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


# ─── ATTRIBUTE VIEWS ──────────────────────────────────────────────────────────

class AttributeDefinitionListView(generics.ListCreateAPIView):
    serializer_class = AttributeDefinitionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = AttributeDefinition.objects.prefetch_related('values').all()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category) | qs.filter(is_global=True)
        return qs


class SpecificationTemplateView(generics.ListCreateAPIView):
    serializer_class = SpecificationTemplateSerializer

    def get_queryset(self):
        return SpecificationTemplate.objects.filter(
            category__slug=self.request.query_params.get('category')
        )


# ─── PRODUCT VIEWS ────────────────────────────────────────────────────────────

class ProductListView(generics.ListAPIView):
    """Public product listing with full filtering, search, sort"""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'brand', 'tags', 'description', 'category__name', 'sub_category__name']
    ordering_fields = ['price', 'discount_price', 'rating', 'review_count', 'created_at', 'stock']
    ordering = ['-created_at']

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, moderation_status=Product.ModerationStatus.APPROVED
        ).select_related('category', 'sub_category', 'supplier')


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, moderation_status=Product.ModerationStatus.APPROVED
        ).prefetch_related('images', 'variants__variant_attributes__attribute', 'variants__variant_attributes__value', 'specifications')


class FeaturedProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True, is_featured=True, moderation_status=Product.ModerationStatus.APPROVED
        ).order_by('-created_at')[:20]


# ─── SUPPLIER PRODUCT VIEWS ───────────────────────────────────────────────────

class SupplierProductListCreateView(generics.ListCreateAPIView):
    """Supplier manages their own products"""
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'brand', 'sku']
    ordering_fields = ['price', 'created_at', 'stock']

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return ProductWriteSerializer
        return ProductListSerializer

    def get_queryset(self):
        return Product.objects.filter(supplier=self.request.user.supplier_profile)

    def perform_create(self, serializer):
        serializer.save(
            supplier=self.request.user.supplier_profile,
            moderation_status=Product.ModerationStatus.PENDING
        )


class SupplierProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductDetailSerializer
        return ProductWriteSerializer

    def get_queryset(self):
        return Product.objects.filter(supplier=self.request.user.supplier_profile)


# ─── PRODUCT IMAGES ───────────────────────────────────────────────────────────

class ProductImageUploadView(generics.ListCreateAPIView):
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return ProductImage.objects.filter(
            product__supplier=self.request.user.supplier_profile,
            product__id=self.kwargs['product_id']
        )

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product, id=self.kwargs['product_id'],
            supplier=self.request.user.supplier_profile
        )
        serializer.save(product=product)


class ProductImageDeleteView(generics.DestroyAPIView):
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]

    def get_queryset(self):
        return ProductImage.objects.filter(
            product__supplier=self.request.user.supplier_profile
        )


# ─── PRODUCT VARIANTS ─────────────────────────────────────────────────────────

class ProductVariantListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductVariantWriteSerializer
        return ProductVariantSerializer

    def get_queryset(self):
        return ProductVariant.objects.filter(
            product__id=self.kwargs['product_id'],
            product__supplier=self.request.user.supplier_profile
        )

    def perform_create(self, serializer):
        product = get_object_or_404(
            Product, id=self.kwargs['product_id'],
            supplier=self.request.user.supplier_profile
        )
        serializer.save(product=product)


class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedSupplier]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductVariantSerializer
        return ProductVariantWriteSerializer

    def get_queryset(self):
        return ProductVariant.objects.filter(
            product__supplier=self.request.user.supplier_profile
        )


# ─── WISHLIST VIEWS ───────────────────────────────────────────────────────────

class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistDeleteView(generics.DestroyAPIView):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


class WishlistToggleView(APIView):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            obj.delete()
            return Response({'wishlisted': False, 'message': 'Removed from wishlist.'})
        return Response({'wishlisted': True, 'message': 'Added to wishlist.'})


# ─── REVIEW VIEWS ─────────────────────────────────────────────────────────────

class ProductReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductReviewSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['rating', 'created_at', 'helpful_count']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return ProductReview.objects.filter(
            product__slug=self.kwargs['slug'], is_approved=True
        ).select_related('user').prefetch_related('images')

    def perform_create(self, serializer):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        serializer.save(user=self.request.user, product=product)

        # Update product rating
        reviews = ProductReview.objects.filter(product=product)
        avg = reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0
        product.rating = round(avg, 2)
        product.review_count = reviews.count()
        product.save(update_fields=['rating', 'review_count'])


# ─── CART VIEWS ───────────────────────────────────────────────────────────────

class CartView(APIView):
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)


class CartItemAddView(APIView):
    def post(self, request):
        print(request.user, '-----request.user--------')
        cart, _ = Cart.objects.get_or_create(user=request.user)
        print(cart, '-------cart---------')
        print(request.data, '------request.data---------')
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data['product']
        variant = serializer.validated_data.get('variant')
        quantity = serializer.validated_data.get('quantity', 1)

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant,
            defaults={'quantity': quantity}
        )
        print(item, created, '-----------item, created---------')
        if not created:
            item.quantity += quantity
            item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartItemUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CartItemSerializer

    def get_queryset(self):
        print(self.request.user, '-----self.request.user------')
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        print(cart, '-----cart-----')
        return CartItem.objects.filter(cart=cart)

    def perform_update(self, serializer):
        if serializer.validated_data.get('quantity', 1) < 1:
            serializer.instance.delete()
        else:
            serializer.save()


class CartClearView(APIView):
    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared.'})


# fix missing import
from django.db import models as dj_models
