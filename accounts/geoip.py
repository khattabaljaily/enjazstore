import ipaddress
import json
import urllib.request

from django.core.cache import cache

LOOKUP_URL = 'http://ip-api.com/json/{ip}?fields=status,message,city,country'
CACHE_TIMEOUT = 60 * 60 * 24  # a day - IP-to-city rarely changes faster than that
REQUEST_TIMEOUT = 2  # seconds - never let a slow geolocation lookup stall a request


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def resolve_location(ip):
    """Best-effort "City, Country" for an IP, cached since it barely ever changes.

    Returns '' for private/loopback addresses or when the lookup fails - the
    caller should treat that as "unknown" rather than an error.
    """
    if not ip:
        return ''

    cache_key = f'geoip:{ip}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    location = ''
    try:
        if not ipaddress.ip_address(ip).is_global:
            location = 'Local network'
        else:
            with urllib.request.urlopen(LOOKUP_URL.format(ip=ip), timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read())
            if data.get('status') == 'success':
                location = ', '.join(filter(None, [data.get('city'), data.get('country')]))
    except (ValueError, OSError):
        location = ''

    cache.set(cache_key, location, CACHE_TIMEOUT)
    return location
