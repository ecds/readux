# Generated by Django 2.2.10 on 2021-06-18 15:52

import apps.ingest.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0008_auto_20210309_1840'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='local',
            options={'verbose_name_plural': 'Local'},
        ),
        migrations.AlterModelOptions(
            name='remote',
            options={'verbose_name_plural': 'Remote'},
        ),
        migrations.AlterField(
            model_name='local',
            name='temp_file_path',
            field=models.FilePathField(default=apps.ingest.models.make_temp_file, path='/var/folders/6q/m6_cn6w96g158vldpfhnn6k40000gn/T/tmph4r5l9ys'),
        ),
    ]
