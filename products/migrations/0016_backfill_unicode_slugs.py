# Category/Product.save() used ASCII-only slugify(), which strips Arabic
# names to an empty string — that empty slug then can't be reversed by any
# URL pattern. Backfills any rows already stuck with a blank slug using the
# same allow_unicode=True slugify the model now uses going forward.

from django.db import migrations
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    for model_name in ('Category', 'Product'):
        model = apps.get_model('products', model_name)
        for obj in model.objects.filter(slug=''):
            base = slugify(obj.name, allow_unicode=True) or f'{model_name.lower()}-{obj.pk}'
            slug = base
            suffix = 1
            while model.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
                suffix += 1
                slug = f'{base}-{suffix}'
            obj.slug = slug
            obj.save(update_fields=['slug'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_zero_out_prices_now_usd'),
    ]

    operations = [
        migrations.RunPython(backfill_slugs, noop_reverse),
    ]
