# Generated by Django 5.0.3 on 2024-08-25 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0015_alter_commande_remise'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commande',
            name='remise',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
    ]
