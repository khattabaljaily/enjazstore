from django.db import migrations


def backfill(apps, schema_editor):
    OrderItem = apps.get_model('orders', 'OrderItem')
    for item in OrderItem.objects.select_related('variant__product').iterator():
        product = item.variant.product
        item.condition = product.condition
        item.warranty_days = product.warranty_days
        item.save(update_fields=['condition', 'warranty_days'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_orderitem_condition_orderitem_warranty_days'),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
