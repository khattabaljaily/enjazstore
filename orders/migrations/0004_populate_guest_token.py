import uuid

from django.db import migrations


def populate_guest_tokens(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.filter(guest_token__isnull=True):
        order.guest_token = uuid.uuid4()
        order.save(update_fields=['guest_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_guest_token'),
    ]

    operations = [
        migrations.RunPython(populate_guest_tokens, migrations.RunPython.noop),
    ]
