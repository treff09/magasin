# Generated by Django 5.0.3 on 2024-08-20 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_pwd_forget'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pwd_forget',
            name='status',
            field=models.CharField(default='0', max_length=1),
        ),
    ]
