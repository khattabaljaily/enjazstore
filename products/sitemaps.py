from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Product


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Category.objects.all()


class StaticViewSitemap(Sitemap):
    changefreq = 'daily'
    priority = 1.0

    def items(self):
        return ['products:list']

    def location(self, item):
        return reverse(item)
