import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_versioned(path):
    """Like {% static %}, but appends the file's mtime as a cache-busting
    query string so edits show up on a normal refresh — in production too,
    not just DEBUG, since that's exactly where stale browser/proxy caches
    otherwise keep serving old CSS/JS after a deploy."""
    url = static(path)
    abs_path = finders.find(path)
    if abs_path:
        url = f"{url}?v={int(os.path.getmtime(abs_path))}"
    return url
