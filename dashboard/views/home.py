from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from orders.models import Order, OrderItem
from products.models import LOW_STOCK_THRESHOLD, Product, Variant

from ..permissions import StaffRequiredMixin

User = get_user_model()

CHART_DAYS = 14


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        orders = Order.objects.all()

        revenue = orders.exclude(status=Order.Status.CANCELLED).aggregate(total=Sum('total'))['total'] or 0

        since = timezone.now() - timedelta(days=CHART_DAYS - 1)
        daily = (
            orders.filter(created_at__gte=since)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Sum('total'))
            .order_by('day')
        )
        daily_map = {row['day']: row['total'] for row in daily}
        today = timezone.localdate()
        chart = []
        for i in range(CHART_DAYS - 1, -1, -1):
            day = today - timedelta(days=i)
            chart.append({'label': day.strftime('%d %b'), 'value': float(daily_map.get(day, 0))})
        max_value = max((point['value'] for point in chart), default=0) or 1
        for point in chart:
            point['height'] = max(round((point['value'] / max_value) * 100), 3 if point['value'] else 0)

        top_products = (
            OrderItem.objects.values('product_name')
            .annotate(qty=Sum('quantity'))
            .order_by('-qty')[:5]
        )

        ctx.update({
            'revenue': revenue,
            'orders_count': orders.count(),
            'pending_orders': orders.filter(status=Order.Status.PENDING).count(),
            'processing_orders': orders.filter(status=Order.Status.PROCESSING).count(),
            'products_count': Product.objects.count(),
            'low_stock': Variant.objects.filter(stock__lte=LOW_STOCK_THRESHOLD).select_related('product').order_by('stock')[:6],
            'customers_count': User.objects.filter(is_staff=False).count(),
            'recent_orders': orders.select_related('user').order_by('-created_at')[:8],
            'chart': chart,
            'top_products': top_products,
        })
        return ctx
