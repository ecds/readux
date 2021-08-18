# Generated by Django 2.2.10 on 2021-08-13 15:14

import apps.ingest.models
import apps.ingest.storages
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0017_auto_20210812_1358'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='local',
            name='temp_file_path',
        ),
        migrations.AlterField(
            model_name='local',
            name='bundle',
            field=models.FileField(storage=apps.ingest.storages.IngestStorage(), upload_to=''),
        ),
        migrations.AlterField(
            model_name='volume',
            name='volume_file',
            field=models.FileField(storage=apps.ingest.storages.IngestStorage(), upload_to=apps.ingest.models.bulk_path),
        ),
    ]
