# Generated by Django 4.1.7 on 2023-03-25 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0031_alter_item_item_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='date_joined',
            field=models.DateField(blank=True, null=True, verbose_name='%Y-%m-%d'),
        ),
    ]
