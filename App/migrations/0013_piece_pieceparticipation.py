# Generated by Django 4.1.3 on 2023-03-01 17:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0012_item_views'),
    ]

    operations = [
        migrations.CreateModel(
            name='Piece',
            fields=[
                ('piece', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('piece_name', models.CharField(max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name='PieceParticipation',
            fields=[
                ('participation', models.AutoField(primary_key=True, serialize=False)),
                ('quantity', models.IntegerField()),
                ('item_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='App.item')),
                ('piece_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='App.piece')),
            ],
        ),
    ]
