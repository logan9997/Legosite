# Generated by Django 4.1.7 on 2023-03-23 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0028_alter_user_date_joined'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='date_joined',
            field=models.DateField(blank=True, default='1991-01-01', null=True, verbose_name='%Y-%m-%d'),
        ),
    ]
