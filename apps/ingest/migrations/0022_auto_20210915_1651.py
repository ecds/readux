# Generated by Django 2.2.23 on 2021-09-15 16:51

import apps.ingest.storages
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0021_auto_20210915_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='local',
            name='bulk',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='local_uploads', to='ingest.Bulk'),
        ),
        migrations.AlterField(
            model_name='bulk',
            name='volume_files',
            field=models.FileField(storage=apps.ingest.storages.IngestStorage(), upload_to=''),
        ),
    ]