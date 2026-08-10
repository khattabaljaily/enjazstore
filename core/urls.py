from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cart.api import (
    CartAddItemView,
    CartApplyCouponView,
    CartDetailView,
    CartRemoveCouponView,
    CartRemoveItemView,
    CartUpdateItemView,
)
from core.views import pwa_manifest, robots_txt, service_worker
from products.api import CategoryViewSet, ProductViewSet
from products.sitemaps import CategorySitemap, ProductSitemap, StaticViewSitemap

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')

api_urlpatterns = [
    path('', include(router.urls)),
    path('cart/', CartDetailView.as_view(), name='api-cart-detail'),
    path('cart/add/', CartAddItemView.as_view(), name='api-cart-add'),
    path('cart/items/<int:item_id>/update/', CartUpdateItemView.as_view(), name='api-cart-update'),
    path('cart/items/<int:item_id>/remove/', CartRemoveItemView.as_view(), name='api-cart-remove'),
    path('cart/apply-coupon/', CartApplyCouponView.as_view(), name='api-cart-apply-coupon'),
    path('cart/remove-coupon/', CartRemoveCouponView.as_view(), name='api-cart-remove-coupon'),
]

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/', include(api_urlpatterns)),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', robots_txt, name='robots'),
    path('sw.js', service_worker, name='service_worker'),
    path('manifest.json', pwa_manifest, name='pwa_manifest'),
    path('accounts/', include('accounts.urls')),
    path('ads/', include('ads.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('', include('pages.urls')),
    path('', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
