from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.utils import timezone

from cart.emails import send_abandoned_cart_reminder
from cart.models import Cart

ABANDONED_AFTER_HOURS = 3


class Command(BaseCommand):
    help = (
        'Emails logged-in customers who left items in their cart without checking out. '
        'Intended to run on a schedule (e.g. every few hours via cron). Guest carts have '
        'no email on file and are skipped.'
    )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=ABANDONED_AFTER_HOURS)
        carts = (
            Cart.objects.filter(user__isnull=False, updated_at__lte=cutoff)
            .filter(Q(abandoned_email_sent_at__isnull=True) | Q(abandoned_email_sent_at__lt=F('updated_at')))
            .select_related('user')
            .prefetch_related('items')
        )

        sent = 0
        for cart in carts:
            if not cart.items.exists():
                continue
            send_abandoned_cart_reminder(cart)
            cart.abandoned_email_sent_at = timezone.now()
            cart.save(update_fields=['abandoned_email_sent_at'])
            sent += 1

        self.stdout.write(f'Sent {sent} abandoned cart reminder(s).')
