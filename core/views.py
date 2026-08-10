import os

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render
from django.urls import reverse


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))
    return render(request, 'robots.txt', {'sitemap_url': sitemap_url}, content_type='text/plain')


def service_worker(request):
    """Serve the PWA service worker from root scope /sw.js."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')


def pwa_manifest(request):
    """Serve the PWA manifest from /manifest.json."""
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    return FileResponse(open(manifest_path, 'rb'), content_type='application/manifest+json')
