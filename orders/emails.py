import logging
import threading
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from payments.registry import get_gateway

logger = logging.getLogger(__name__)

LOGO_PATH = settings.BASE_DIR / 'static' / 'img' / 'logo' / 'logo.png'
LOGO_CID = 'enjaz-logo'

try:
    with open(LOGO_PATH, 'rb') as _logo_file:
        _LOGO_BYTES = _logo_file.read()
except FileNotFoundError:
    _LOGO_BYTES = None

STATUS_COLORS = {
    'pending': '#62787a',
    'processing': '#0f4c5c',
    'shipped': '#fcb503',
    'delivered': '#0fb07e',
    'cancelled': '#e0473a',
}

STATUS_MESSAGES = {
    'processing': 'طلبك قيد التجهيز.',
    'shipped': 'طلبك في الطريق إليك.',
    'delivered': 'تم توصيل طلبك. نتمنى أن ينال إعجابك!',
    'cancelled': 'تم إلغاء طلبك.',
}

RETURN_STATUS_COLORS = {
    'pending': '#0f4c5c',
    'approved': '#0fb07e',
    'rejected': '#e0473a',
    'completed': '#29c94f',
}


def _send(request, template_prefix, subject, to_email, context):
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


def send_new_order_admin_alert(request, order):
    order_url = request.build_absolute_uri(reverse('dashboard:order_detail', args=[order.pk]))

    for _, admin_email in settings.ADMINS:
        _send(
            request, 'new_order_admin_alert',
            subject=f'طلب جديد #{order.id} — {order.total} ج.س — إنجاز',
            to_email=admin_email,
            context={
                'order': order,
                'items': order.items.select_related('variant').all(),
                'order_url': order_url,
            },
        )


def send_order_confirmation(request, order):
    order_url = request.build_absolute_uri(reverse('orders:detail', args=[order.guest_token]))
    gateway = get_gateway(order.payment.gateway) if hasattr(order, 'payment') else None

    _send(
        request, 'order_confirmation',
        subject=f'تم تأكيد الطلب #{order.id} — إنجاز',
        to_email=order.email,
        context={
            'order': order,
            'items': order.items.select_related('variant').all(),
            'order_url': order_url,
            'payment_method_label': gateway.label if gateway else '—',
        },
    )


def send_order_status_update(request, order):
    order_url = request.build_absolute_uri(reverse('orders:detail', args=[order.guest_token]))

    _send(
        request, 'order_status_update',
        subject=f'الطلب #{order.id} — {order.get_status_display()} — إنجاز',
        to_email=order.email,
        context={
            'order': order,
            'order_url': order_url,
            'status_color': STATUS_COLORS.get(order.status, '#0f4c5c'),
            'status_message': STATUS_MESSAGES.get(order.status, 'Your order status has changed.'),
        },
    )


def send_return_request_received(request, return_request):
    order = return_request.order
    order_url = request.build_absolute_uri(reverse('orders:detail', args=[order.guest_token]))

    _send(
        request, 'return_request_received',
        subject=f'تم استلام طلب الإرجاع — الطلب #{order.id} — إنجاز',
        to_email=order.email,
        context={
            'order': order,
            'return_request': return_request,
            'order_url': order_url,
        },
    )


def send_return_request_status_update(request, return_request):
    order = return_request.order
    order_url = request.build_absolute_uri(reverse('orders:detail', args=[order.guest_token]))

    _send(
        request, 'return_request_status_update',
        subject=f'تحديث طلب الإرجاع — الطلب #{order.id} — إنجاز',
        to_email=order.email,
        context={
            'order': order,
            'return_request': return_request,
            'order_url': order_url,
            'status_color': RETURN_STATUS_COLORS.get(return_request.status, '#0f4c5c'),
        },
    )
