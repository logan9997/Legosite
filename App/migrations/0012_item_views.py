# Generated by Django 4.1.3 on 2023-02-11 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0011_alter_user_date_joined'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='views',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
