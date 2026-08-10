from django.conf import settings
from django.http import Http404


class AdminAccessMiddleware:
    """Hides the admin behind an existing superuser session.

    Anyone hitting the admin path without already being logged in as a
    superuser (via the normal site login) gets a plain 404, not Django's
    admin login form, so the path's existence isn't revealed to probing.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = '/' + settings.ADMIN_URL

    def __call__(self, request):
        if request.path.startswith(self.admin_prefix):
            if not (request.user.is_authenticated and request.user.is_superuser):
                raise Http404
        return self.get_response(request)
