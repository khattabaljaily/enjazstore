from django.utils import timezone

from .geoip import get_client_ip, resolve_location

ACTIVITY_THROTTLE = timezone.timedelta(minutes=5)


class TrackUserActivityMiddleware:
    """Keeps last_seen_at/ip/location fresh for the registered-users list.

    Throttled to once per ACTIVITY_THROTTLE per user so a user browsing the
    site doesn't trigger a write (and a geolocation lookup) on every request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            now = timezone.now()
            if not user.last_seen_at or now - user.last_seen_at >= ACTIVITY_THROTTLE:
                ip = get_client_ip(request)
                user.last_seen_at = now
                update_fields = ['last_seen_at']
                if ip and ip != user.last_seen_ip:
                    user.last_seen_ip = ip
                    user.last_seen_location = resolve_location(ip)
                    update_fields += ['last_seen_ip', 'last_seen_location']
                user.save(update_fields=update_fields)

        return response
