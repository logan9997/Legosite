# Generated by Django 4.1.7 on 2023-04-04 18:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0033_alter_item_item_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='date_joined',
        ),
    ]
