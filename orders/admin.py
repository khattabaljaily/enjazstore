from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Order, OrderItem, ReturnRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'variant', 'product_name', 'variant_label', 'unit_price', 'quantity', 'condition', 'warranty_days',
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'status', 'total', 'created_at', 'bill_link')
    list_editable = ('status',)
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

    def bill_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">View / print bill</a>',
            reverse('dashboard:order_bill', args=[obj.pk]),
        )
    bill_link.short_description = 'Bill'


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'reason', 'resolution_requested', 'status', 'created_at')
    list_filter = ('status', 'reason', 'resolution_requested')
    search_fields = ('order__full_name', 'order__email')
