from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ELinkUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Contact info', {'fields': ('phone', 'address', 'city')}),
        ('Dashboard role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
