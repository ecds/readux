# Generated by Django 2.2.23 on 2021-09-20 21:30

import apps.ingest.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0024_auto_20210916_1809'),
    ]

    operations = [
        migrations.AddField(
            model_name='local',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='bulk',
            name='volume_files',
            field=models.FileField(upload_to=apps.ingest.models.bulk_path),
        ),
    ]
