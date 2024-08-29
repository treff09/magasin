
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0013_merge_20240824_2305'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='remise',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
