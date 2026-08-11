from django.views.generic import TemplateView

from products.models import Variant
from products.pricing import get_exchange_rate, to_sdg

from ..permissions import ManagerRequiredMixin


class StockValueReportView(ManagerRequiredMixin, TemplateView):
    template_name = 'dashboard/stock_value.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        variants = (
            Variant.objects.filter(stock__gt=0)
            .select_related('product', 'product__category')
            .order_by('product__category__name', 'product__name', 'size', 'color')
        )

        rate = get_exchange_rate()
        groups_by_category = {}
        grand_total = 0
        for variant in variants:
            # Variant.price is USD (catalog reference price); this report values
            # current inventory in real money, so convert to SDG here.
            price = to_sdg(variant.price, rate)
            total = variant.stock * price
            grand_total += total

            category = variant.product.category
            group = groups_by_category.setdefault(category.id, {
                'category': category,
                'items': [],
                'total': 0,
            })
            group['items'].append({
                'label': str(variant),
                'qty': variant.stock,
                'price': price,
                'total': total,
            })
            group['total'] += total

        category_groups = sorted(groups_by_category.values(), key=lambda g: g['category'].name)

        ctx.update({
            'category_groups': category_groups,
            'grand_total': grand_total,
        })
        return ctx
