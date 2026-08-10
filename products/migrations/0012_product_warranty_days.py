from django.db import migrations, models


def months_to_days(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.exclude(warranty_days=None):
        product.warranty_days = product.warranty_days * 30
        product.save(update_fields=['warranty_days'])


def days_to_months(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.exclude(warranty_days=None):
        product.warranty_days = max(product.warranty_days // 30, 1)
        product.save(update_fields=['warranty_days'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_product_condition_alter_product_warranty_months'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='warranty_months',
            new_name='warranty_days',
        ),
        migrations.RunPython(months_to_days, days_to_months),
        migrations.AlterField(
            model_name='product',
            name='warranty_days',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                help_text="Warranty period in days. Leave blank if this product carries no warranty. "
                          "For used products, warranty is typically short (7-30 days).",
            ),
        ),
    ]
