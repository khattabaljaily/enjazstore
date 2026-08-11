from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageOps

PRODUCT_IMAGE_MAX_DIMENSION = 1600
LOW_STOCK_THRESHOLD = 5
NEW_BADGE_DAYS = 14


def optimize_product_image(image_field):
    """Downscale + recompress an uploaded image, preserving transparency where present."""
    img = Image.open(image_field)
    img = ImageOps.exif_transpose(img)
    has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)

    img.thumbnail((PRODUCT_IMAGE_MAX_DIMENSION, PRODUCT_IMAGE_MAX_DIMENSION), Image.LANCZOS)

    buffer = BytesIO()
    if has_alpha:
        img.convert('RGBA').save(buffer, format='PNG', optimize=True)
        ext, content_type = 'png', 'image/png'
    else:
        img.convert('RGB').save(buffer, format='JPEG', quality=82, optimize=True)
        ext, content_type = 'jpg', 'image/jpeg'
    buffer.seek(0)

    name = f'{image_field.name.rsplit(".", 1)[0]}.{ext}'
    return InMemoryUploadedFile(buffer, 'ImageField', name, content_type, buffer.getbuffer().nbytes, None)


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, blank=True,
        help_text='Font Awesome icon name, e.g. "shopping-bag" for the fa-shopping-bag icon.',
    )

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:list_by_category', kwargs={'slug': self.slug})


class Product(models.Model):
    class Condition(models.TextChoices):
        NEW = 'new', 'جديد'
        USED = 'used', 'مستعمل'

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    # USD, not SDG — converted to SDG for display/checkout using
    # SiteSettings.usd_to_sdg_rate (see products/pricing.py), so it doesn't
    # need repricing every time the exchange rate moves.
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='بالدولار الأمريكي (USD)')
    condition = models.CharField(max_length=10, choices=Condition.choices, default=Condition.NEW)
    warranty_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Warranty period in days. Leave blank if this product carries no warranty. "
                   "For used products, warranty is typically short (7-30 days).",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show a 'Bestseller' badge on this product.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})

    @property
    def main_image(self):
        return self.images.first()

    @property
    def is_new(self):
        return timezone.now() - self.created_at < timedelta(days=NEW_BADGE_DAYS)

    @property
    def is_used(self):
        return self.condition == self.Condition.USED

    @property
    def total_stock(self):
        return sum(v.stock for v in self.variants.all())

    @property
    def default_variant(self):
        in_stock = [v for v in self.variants.all() if v.stock > 0]
        return in_stock[0] if in_stock else None

    @property
    def approved_reviews(self):
        return self.reviews.filter(status=Review.Status.APPROVED)

    @property
    def rating_summary(self):
        agg = self.approved_reviews.aggregate(average=Avg('rating'), count=Count('id'))
        average = agg['average'] or 0
        return {'average': average, 'count': agg['count'], 'stars_full': round(average)}

    def has_purchased(self, user):
        if not user.is_authenticated:
            return False
        from orders.models import OrderItem
        return OrderItem.objects.filter(
            order__user=user, variant__product=self,
        ).exclude(order__status='cancelled').exists()

    def has_reviewed(self, user):
        if not user.is_authenticated:
            return False
        return self.reviews.filter(user=user).exists()

    def can_review(self, user):
        return self.has_purchased(user) and not self.has_reviewed(user)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f'{self.product.name} image'

    def save(self, *args, **kwargs):
        if self.image and isinstance(self.image.file, UploadedFile):
            self.image = optimize_product_image(self.image)
        super().save(*args, **kwargs)


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    sku = models.CharField(max_length=64, unique=True)
    stock = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='بالدولار الأمريكي (USD). اتركه فارغًا لاستخدام سعر المنتج.',
    )

    class Meta:
        unique_together = ('product', 'size', 'color')

    def __str__(self):
        parts = [p for p in (self.size, self.color) if p]
        label = ' / '.join(parts) if parts else self.sku
        return f'{self.product.name} ({label})'

    @property
    def price(self):
        return self.price_override if self.price_override is not None else self.product.price

    @property
    def in_stock(self):
        return self.stock > 0


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.product}'


class StockSubscription(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='stock_subscriptions')
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('variant', 'email')

    def __str__(self):
        return f'{self.email} — {self.variant}'


class Review(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'قيد المراجعة'
        APPROVED = 'approved', 'مقبول'
        REJECTED = 'rejected', 'مرفوض'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f'{self.rating}★ review of {self.product.name} by {self.user}'
