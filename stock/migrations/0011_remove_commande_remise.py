# Generated by Django 5.0.3 on 2024-08-19 22:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0010_commande_remise'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commande',
            name='remise',
        ),
    ]
