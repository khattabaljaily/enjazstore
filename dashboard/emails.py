import logging
import threading
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)

LOGO_PATH = settings.BASE_DIR / 'static' / 'img' / 'logo' / 'logo.png'
LOGO_CID = 'elink-logo'

try:
    with open(LOGO_PATH, 'rb') as _logo_file:
        _LOGO_BYTES = _logo_file.read()
except FileNotFoundError:
    _LOGO_BYTES = None


def _send(subject, to_email, context):
    if not to_email:
        return

    context = {**context, 'logo_cid': LOGO_CID}
    html_body = render_to_string('emails/marketing_broadcast.html', context)
    text_body = render_to_string('emails/marketing_broadcast.txt', context)

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
            logger.exception('Failed to send marketing broadcast to %s', to_email)

    # SMTP delivery can block for seconds (or hang) on a slow/unreachable mail
    # server; run it off the request thread so it never delays the HTTP response.
    threading.Thread(target=_deliver, daemon=True).start()


def send_marketing_broadcast(request, subject, body, recipient_emails):
    shop_url = request.build_absolute_uri(reverse('products:list'))
    paragraphs = [p.strip() for p in body.replace('\r\n', '\n').split('\n\n') if p.strip()]

    for email in recipient_emails:
        _send(subject, email, {
            'subject': subject,
            'paragraphs': paragraphs,
            'shop_url': shop_url,
        })
