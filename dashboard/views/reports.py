import csv
from datetime import timedelta

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from orders.models import Order, OrderItem

from ..permissions import ManagerRequiredMixin

ALLOWED_RANGES = (7, 30, 90)


def _resolve_days(request):
    try:
        days = int(request.GET.get('days', 30))
    except ValueError:
        days = 30
    return days if days in ALLOWED_RANGES else 30


class ReportsView(ManagerRequiredMixin, TemplateView):
    template_name = 'dashboard/reports.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        days = _resolve_days(self.request)
        since = timezone.now() - timedelta(days=days - 1)
        orders = Order.objects.filter(created_at__gte=since)
        counted_orders = orders.exclude(status=Order.Status.CANCELLED)

        revenue = counted_orders.aggregate(total=Sum('total'))['total'] or 0

        by_status = Order.objects.filter(created_at__gte=since).values('status').annotate(count=Count('id')).order_by('-count')

        line_items = OrderItem.objects.filter(order__created_at__gte=since).exclude(order__status=Order.Status.CANCELLED)

        top_products = (
            line_items.values('product_name')
            .annotate(qty=Sum('quantity'), revenue=Sum(F('unit_price') * F('quantity')))
            .order_by('-qty')[:8]
        )

        top_categories = (
            line_items.values('variant__product__category__name')
            .annotate(qty=Sum('quantity'), revenue=Sum(F('unit_price') * F('quantity')))
            .order_by('-revenue')[:8]
        )

        daily = (
            counted_orders.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Sum('total'))
            .order_by('day')
        )
        daily_map = {row['day']: row['total'] for row in daily}
        today = timezone.localdate()
        chart = []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            chart.append({'label': day.strftime('%d %b'), 'value': float(daily_map.get(day, 0))})
        max_value = max((point['value'] for point in chart), default=0) or 1
        for point in chart:
            point['height'] = max(round((point['value'] / max_value) * 100), 3 if point['value'] else 0)

        ctx.update({
            'days': days,
            'allowed_ranges': ALLOWED_RANGES,
            'revenue': revenue,
            'orders_count': counted_orders.count(),
            'by_status': by_status,
            'top_products': top_products,
            'top_categories': top_categories,
            'chart': chart,
        })
        return ctx


class ReportsExportView(ManagerRequiredMixin, View):
    def get(self, request):
        days = _resolve_days(request)
        since = timezone.now() - timedelta(days=days - 1)
        orders = Order.objects.filter(created_at__gte=since).order_by('-created_at')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="orders_last_{days}_days.csv"'

        writer = csv.writer(response)
        writer.writerow(['رقم الطلب', 'التاريخ', 'العميل', 'البريد الإلكتروني', 'الحالة', 'الإجمالي (ج.س)'])
        for order in orders:
            writer.writerow([
                order.id,
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.full_name,
                order.email,
                order.get_status_display(),
                order.total,
            ])
        return response
