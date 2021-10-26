# Generated by Django 2.2.24 on 2021-10-26 17:36

import apps.ingest.models
import apps.ingest.storages
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0031_ingesttaskwatcher_associated_manifest'),
    ]

    operations = [
        migrations.AddField(
            model_name='local',
            name='bundle_from_bulk',
            field=models.FileField(null=True, upload_to=apps.ingest.models.bulk_path),
        ),
        migrations.AlterField(
            model_name='local',
            name='bundle',
            field=models.FileField(null=True, storage=apps.ingest.storages.IngestStorage(), upload_to=''),
        ),
    ]
