from django.core.management.base import BaseCommand

from products.emails import send_low_stock_digest
from products.models import LOW_STOCK_THRESHOLD, Variant


class Command(BaseCommand):
    help = 'Emails admins a digest of variants at or below the low-stock threshold. Intended to run on a schedule (e.g. daily via cron).'

    def handle(self, *args, **options):
        variants = list(
            Variant.objects.filter(stock__lte=LOW_STOCK_THRESHOLD)
            .select_related('product')
            .order_by('stock'),
        )

        if not variants:
            self.stdout.write('No low-stock variants — nothing to send.')
            return

        send_low_stock_digest(variants)
        self.stdout.write(f'Sent low-stock digest for {len(variants)} variant(s).')
