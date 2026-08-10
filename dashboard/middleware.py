import hashlib
from datetime import date

from django.conf import settings as django_settings
from django.shortcuts import render

from accounts.geoip import get_client_ip, resolve_location

from .models import SiteSettings, VisitLog

ALLOWED_PREFIXES = (
    '/dashboard/', '/' + django_settings.ADMIN_URL, '/accounts/', '/static/', '/media/',
    '/robots.txt', '/sitemap.xml', '/sw.js', '/manifest.json',
)


class ComingSoonMiddleware:
    """Shows a coming soon page to visitors while maintenance_mode is on.

    Staff always pass through, and the dashboard/admin/accounts paths stay
    reachable so staff can log in and switch the mode back off.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(ALLOWED_PREFIXES):
            return self.get_response(request)

        if request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)

        settings = SiteSettings.load()
        if settings.maintenance_mode:
            return render(request, 'coming_soon.html', {'message': settings.coming_soon_message}, status=503)

        return self.get_response(request)


class VisitorTrackingMiddleware:
    """Logs one VisitLog row per real page view for the admin's visitor
    analytics report - approximate city (via IP geolocation) and whether
    the visitor was signed in. Staff browsing the site isn't counted.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, 'user', None)
        is_staff = user is not None and user.is_authenticated and user.is_staff
        is_page_view = (
            request.method == 'GET'
            and response.status_code == 200
            and response.get('Content-Type', '').startswith('text/html')
            and not is_staff
        )
        if is_page_view:
            ip = get_client_ip(request)
            visitor_hash = hashlib.sha256(
                f'{ip}:{request.META.get("HTTP_USER_AGENT", "")}:{date.today()}:{django_settings.SECRET_KEY}'.encode(),
            ).hexdigest()
            VisitLog.objects.create(
                location=resolve_location(ip),
                visitor_hash=visitor_hash,
                user=user if (user is not None and user.is_authenticated) else None,
            )

        return response
