# Generated by Django 2.2.10 on 2021-08-05 17:31

import apps.ingest.models
from django.db import migrations, models
import storages.backends.s3boto3
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0008_auto_20210309_1840'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bulk',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='BulkUploads',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('volume_file', models.FileField(storage=storages.backends.s3boto3.S3Boto3Storage, upload_to=apps.ingest.models.bulk_path)),
            ],
        ),
        migrations.AlterModelOptions(
            name='local',
            options={'verbose_name_plural': 'Local'},
        ),
        migrations.AlterModelOptions(
            name='remote',
            options={'verbose_name_plural': 'Remote'},
        ),
    ]
