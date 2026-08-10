import django_filters
from django.db.models import Case, IntegerField, Q, Value, When

from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    q = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price', 'q']

    def filter_search(self, queryset, name, value):
        terms = value.split()
        if not terms:
            return queryset

        for term in terms:
            queryset = queryset.filter(
                Q(name__icontains=term) | Q(description__icontains=term) | Q(category__name__icontains=term),
            )

        # Products whose name contains the full phrase rank above matches
        # that only hit the description or category (still relevant, but
        # a looser match), so an exact-ish name match always surfaces first.
        return queryset.annotate(
            name_match=Case(
                When(name__icontains=value, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        ).order_by('name_match', '-created_at')
