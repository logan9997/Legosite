# Generated by Django 4.1.3 on 2023-01-23 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0006_alter_watchlist_date_added'),
    ]

    operations = [
        migrations.AlterField(
            model_name='price',
            name='date',
            field=models.DateField(blank=True, default='1991-01-01', null=True, verbose_name='%Y-%m-%d'),
        ),
        migrations.AlterField(
            model_name='watchlist',
            name='date_added',
            field=models.DateField(verbose_name='%Y-%m-%d'),
        ),
    ]
