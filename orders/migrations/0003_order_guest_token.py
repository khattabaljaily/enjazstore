from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_delivered_at_returnrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='guest_token',
            field=models.UUIDField(editable=False, null=True),
        ),
    ]
