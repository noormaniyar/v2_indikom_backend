from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

# ─── FILE PATHS ───────────────────────────────────────────────────────────────
category_images_path = "category/files/"
sub_category_images_path = "sub_category/files/"
product_images_path = "product/files/"
product_ar_images_path = "product/ar/files/"


# ─── CATEGORY (Multi-level using MPTT - unlimited depth like Amazon) ──────────
class Category(MPTTModel):
    """
    Multi-level category tree: Appliances > Kitchen > Toaster
    Uses django-mptt for efficient tree queries.
    Your existing Category fields are preserved; parent field added for multi-level support.
    """
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True, related_name='children'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    thumbnail = models.FileField(upload_to=category_images_path, blank=True, null=True)
    icon = models.FileField(upload_to=category_images_path, blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        """Returns: Appliances > Kitchen > Toaster"""
        ancestors = self.get_ancestors(include_self=True)
        return ' > '.join([a.name for a in ancestors])


# ─── SUB CATEGORY (kept for backward compatibility with your existing code) ───
class SubCategory(models.Model):
    """
    Kept for backward compatibility with your existing Product FK.
    For new categories, prefer using Category.parent (MPTT tree).
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sub_categories')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    thumbnail = models.FileField(upload_to=sub_category_images_path, blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Sub Categories'

    def __str__(self):
        return f"{self.category.name} > {self.name}"


# ─── SPECIFICATION TEMPLATE ───────────────────────────────────────────────────
class SpecificationTemplate(models.Model):
    """Defines spec keys for a category (e.g., 'Wattage', 'Material', 'Dimensions')"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='spec_templates')
    key = models.CharField(max_length=100)        # e.g., "Wattage"
    unit = models.CharField(max_length=20, blank=True)  # e.g., "W", "cm", "kg"
    is_filterable = models.BooleanField(default=False)  # Show in filter sidebar?
    sort_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ['category', 'key']
        ordering = ['sort_order', 'key']

    def __str__(self):
        return f"{self.category.name} - {self.key}"


# ─── VARIANT ATTRIBUTE DEFINITIONS ───────────────────────────────────────────
class AttributeDefinition(models.Model):
    """Defines variant attribute types per category (e.g., 'Color', 'Size', 'Material')"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='attribute_definitions', null=True, blank=True)
    name = models.CharField(max_length=100)   # e.g., "Color", "Size"
    is_global = models.BooleanField(default=False)  # True = applies across all categories
    sort_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.name}"


class AttributeValue(models.Model):
    """Possible values for an attribute (e.g., Color: Red, Blue, Green)"""
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)      # e.g., "Red"
    display_value = models.CharField(max_length=100, blank=True)  # e.g., "#FF0000" for color hex
    sort_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ['attribute', 'value']
        ordering = ['sort_order', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# ─── PRODUCT ──────────────────────────────────────────────────────────────────
class Product(models.Model):
    """
    Your existing Product model fields preserved exactly.
    Added: brand, slug, discount_price, rating, review_count, tags,
           is_featured, meta_title, meta_description for SEO.
    """
    from apps.accounts.models import SupplierProfile

    class ModerationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        DRAFT = 'draft', 'Draft'

    # ── Your existing fields (unchanged) ─────────────────────────────────────
    supplier = models.ForeignKey(
        'accounts.SupplierProfile', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='products'
    )
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='products'
    )
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='products'
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    thumbnail = models.FileField(upload_to=product_images_path, blank=True, null=True)
    file = models.FileField(upload_to=product_images_path, blank=True, null=True)
    ar_file = models.FileField(upload_to=product_ar_images_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── New fields ────────────────────────────────────────────────────────────
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')
    moderation_status = models.CharField(
        max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text='In kg')
    dimensions = models.CharField(max_length=100, blank=True, help_text='L x W x H in cm')
    has_ar = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.ar_file:
            self.has_ar = True
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            base_slug = slugify(self.name)
            self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        if self.discount_price and self.price > 0:
            return round(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def effective_price(self):
        return self.discount_price if self.discount_price else self.price


# ─── PRODUCT IMAGES ───────────────────────────────────────────────────────────
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to=product_images_path)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.name}"


# ─── PRODUCT VARIANT ─────────────────────────────────────────────────────────
class ProductVariant(models.Model):
    """
    Multi-level variants: Product > Variant (3-Seater / Light Grey / Wool)
    Each variant has its own price, stock, SKU, and images.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                help_text='Leave blank to inherit from product')
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    thumbnail = models.FileField(upload_to=product_images_path, blank=True, null=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        attrs = ' / '.join([f"{va.attribute.name}: {va.value.value}" for va in self.variant_attributes.all()])
        return f"{self.product.name} - [{attrs}]"

    @property
    def effective_price(self):
        p = self.price or self.product.price
        d = self.discount_price or self.product.discount_price
        return d if d else p

    @property
    def variant_label(self):
        return ' / '.join([va.value.value for va in self.variant_attributes.select_related('value').all()])


class VariantAttribute(models.Model):
    """Links a variant to its attribute values"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='variant_attributes')
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['variant', 'attribute']

    def __str__(self):
        return f"{self.attribute.name}: {self.value.value}"


# ─── PRODUCT SPECIFICATIONS ───────────────────────────────────────────────────
class ProductSpecification(models.Model):
    """Key-value specs: e.g., Wattage: 300W, Material: Stainless Steel"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=500)
    unit = models.CharField(max_length=20, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'key']

    def __str__(self):
        return f"{self.product.name}: {self.key} = {self.value}{self.unit}"


# ─── WISHLIST ─────────────────────────────────────────────────────────────────
class Wishlist(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"


# ─── PRODUCT REVIEW ───────────────────────────────────────────────────────────
class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reviews')
    order_item = models.OneToOneField(
        'orders.OrderItem', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='review'
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}★)"


class ReviewImage(models.Model):
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='images')
    image = models.FileField(upload_to='reviews/images/')

    def __str__(self):
        return f"Image for review {self.review.id}"


# ─── CART ─────────────────────────────────────────────────────────────────────
class Cart(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.email}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def unit_price(self):
        if self.variant:
            return self.variant.effective_price
        return self.product.effective_price

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
