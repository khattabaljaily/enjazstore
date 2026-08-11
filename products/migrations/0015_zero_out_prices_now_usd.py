# Product/Variant prices now mean USD, not SDG. Existing values were entered
# under the old (SDG) meaning, so leaving them as numbers would silently
# misprice everything (e.g. a product that cost 5,000 ج.س would now read as
# $5,000). Zeroing them forces a deliberate re-entry in USD rather than a
# silent, wrong carry-over.

from django.db import migrations


def zero_out_prices(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Variant = apps.get_model('products', 'Variant')
    Product.objects.update(price=0)
    Variant.objects.update(price_override=None)


def noop_reverse(apps, schema_editor):
    """Not reversible — the original SDG values aren't recoverable."""


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0014_alter_product_price_alter_variant_price_override'),
    ]

    operations = [
        migrations.RunPython(zero_out_prices, noop_reverse),
    ]
