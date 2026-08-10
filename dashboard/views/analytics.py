from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from ..models import VisitLog
from ..permissions import ManagerRequiredMixin
from .reports import ALLOWED_RANGES, _resolve_days

TOP_LOCATIONS_COUNT = 10


class VisitorAnalyticsView(ManagerRequiredMixin, TemplateView):
    template_name = 'dashboard/analytics.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        days = _resolve_days(self.request)
        since = timezone.now() - timedelta(days=days - 1)
        visits = VisitLog.objects.filter(created_at__gte=since)

        registered_visits = visits.filter(user__isnull=False)
        anonymous_visits = visits.filter(user__isnull=True)
        unique_visitors = (
            registered_visits.values('user_id').distinct().count()
            + anonymous_visits.values('visitor_hash').distinct().count()
        )

        top_locations = (
            visits.values('location').annotate(count=Count('id')).order_by('-count')[:TOP_LOCATIONS_COUNT]
        )

        daily = (
            visits.annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Count('id'))
            .order_by('day')
        )
        daily_map = {row['day']: row['total'] for row in daily}
        today = timezone.localdate()
        chart = []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            chart.append({'label': day.strftime('%d %b'), 'value': daily_map.get(day, 0)})
        max_value = max((point['value'] for point in chart), default=0) or 1
        for point in chart:
            point['height'] = max(round((point['value'] / max_value) * 100), 3 if point['value'] else 0)

        ctx.update({
            'days': days,
            'allowed_ranges': ALLOWED_RANGES,
            'total_visits': visits.count(),
            'unique_visitors': unique_visitors,
            'registered_count': registered_visits.count(),
            'anonymous_count': anonymous_visits.count(),
            'top_locations': top_locations,
            'chart': chart,
        })
        return ctx
