# Generated by Django 2.2.10 on 2021-08-12 13:58

import apps.ingest.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0016_auto_20210812_1339'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='local',
            name='bundle_local',
        ),
        migrations.AddField(
            model_name='local',
            name='local_bundle_path',
            field=models.CharField(blank=True, max_length=100, null=True),
        )
    ]
