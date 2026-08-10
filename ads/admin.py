from django.contrib import admin

from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('name', 'placement', 'is_active', 'order', 'created_at')
    list_filter = ('placement', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
