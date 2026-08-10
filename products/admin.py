from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage, Variant


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'preview', 'alt_text', 'is_primary')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;object-fit:cover;">', obj.image.url)
        return '—'
    preview.short_description = 'Preview'


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ('size', 'color', 'sku', 'stock', 'price_override')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'condition', 'price', 'is_active', 'total_stock')
    list_display_links = ('thumbnail', 'name')
    list_editable = ('price', 'is_active')
    list_filter = ('category', 'condition', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, VariantInline]

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category', 'description')}),
        ('Pricing & visibility', {'fields': ('price', 'is_active')}),
        ('Condition & warranty', {'fields': ('condition', 'warranty_days')}),
    )

    def thumbnail(self, obj):
        image = obj.main_image
        if image:
            return format_html('<img src="{}" style="height:44px;width:44px;border-radius:6px;object-fit:cover;">', image.image.url)
        return '—'
    thumbnail.short_description = ''
