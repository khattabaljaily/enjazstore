from django.db.models import F
from django.shortcuts import get_object_or_404, redirect

from .models import Banner


def banner_click(request, pk):
    banner = get_object_or_404(Banner, pk=pk, is_active=True)
    Banner.objects.filter(pk=banner.pk).update(clicks=F('clicks') + 1)
    return redirect(banner.target_url)
