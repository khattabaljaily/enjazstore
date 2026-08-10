import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_populate_guest_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='guest_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
