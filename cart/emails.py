import logging
import threading
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)

LOGO_PATH = settings.BASE_DIR / 'static' / 'img' / 'logo' / 'logo.png'
LOGO_CID = 'enjaz-logo'

try:
    with open(LOGO_PATH, 'rb') as _logo_file:
        _LOGO_BYTES = _logo_file.read()
except FileNotFoundError:
    _LOGO_BYTES = None


def _send(template_prefix, subject, to_email, context):
    if not to_email:
        return

    context = {**context, 'logo_cid': LOGO_CID}
    html_body = render_to_string(f'emails/{template_prefix}.html', context)
    text_body = render_to_string(f'emails/{template_prefix}.txt', context)

    message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email])
    message.attach_alternative(html_body, 'text/html')

    if _LOGO_BYTES is not None:
        message.mixed_subtype = 'related'
        logo = MIMEImage(_LOGO_BYTES)
        logo.add_header('Content-ID', f'<{LOGO_CID}>')
        logo.add_header('Content-Disposition', 'inline', filename='logo.png')
        message.attach(logo)

    def _deliver():
        try:
            message.send()
        except Exception:
            logger.exception('Failed to send "%s" email to %s', template_prefix, to_email)

    # SMTP delivery can block for seconds (or hang) on a slow/unreachable mail
    # server; run it off the request thread so it never delays the HTTP response.
    threading.Thread(target=_deliver, daemon=True).start()


def send_abandoned_cart_reminder(cart):
    cart_url = settings.SITE_URL.rstrip('/') + reverse('cart:detail')

    _send(
        'abandoned_cart_reminder',
        subject="نسيت شيئًا في سلتك — إنجاز ستور",
        to_email=cart.user.email,
        context={
            'user': cart.user,
            'items': cart.items.select_related('variant__product'),
            'cart_url': cart_url,
        },
    )
