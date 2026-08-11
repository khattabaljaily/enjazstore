from django.urls import path, register_converter

from . import views


class UnicodeSlugConverter:
    """Like Django's built-in `slug` converter, but not ASCII-only — category
    and product names here are Arabic, and slugify(name, allow_unicode=True)
    produces Arabic slugs, so the URL pattern needs to accept them too."""
    regex = r'[-\w]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(UnicodeSlugConverter, 'uslug')

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('category/<uslug:slug>/', views.product_list, name='list_by_category'),
    path('product/<uslug:slug>/', views.product_detail, name='detail'),
    path('product/<uslug:slug>/review/', views.submit_review, name='submit_review'),
    path('product/<uslug:slug>/notify-stock/', views.subscribe_stock, name='notify_stock'),
    path('product/<uslug:slug>/wishlist-toggle/', views.toggle_wishlist, name='toggle_wishlist'),
]
