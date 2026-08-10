from django.db.models import F

from dashboard.models import SiteSettings

from .models import Banner


def banners(request):
    if request.path.startswith('/api/') or request.path.startswith('/dashboard/'):
        return {}

    if not SiteSettings.load().ads_enabled:
        return {'banners': {}, 'ads_enabled': False}

    by_placement = {}
    for banner in Banner.objects.filter(is_active=True):
        by_placement.setdefault(banner.placement, banner)

    if by_placement:
        Banner.objects.filter(pk__in=[b.pk for b in by_placement.values()]).update(
            impressions=F('impressions') + 1,
        )

    return {'banners': by_placement, 'ads_enabled': True}
