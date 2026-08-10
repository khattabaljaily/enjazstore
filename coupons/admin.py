from django.contrib import admin

from .models import Coupon, CouponRedemption


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'amount', 'is_active', 'redemption_count', 'max_redemptions', 'valid_until')
    search_fields = ('code',)


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'order', 'email', 'amount_applied', 'created_at')
    search_fields = ('coupon__code', 'email')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
