# Generated by Django 2.2.23 on 2021-09-16 18:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0023_auto_20210916_1803'),
    ]

    operations = [
        migrations.AlterField(
            model_name='local',
            name='bulk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='local_uploads', to='ingest.Bulk'),
        ),
    ]
