# Generated by Django 2.2.10 on 2021-08-05 17:48

import apps.ingest.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0010_auto_20210805_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='volume',
            name='bulk',
            field=models.ForeignKey(default='6b48744e-30a6-4de3-8ff5-5a527cf48e4e', on_delete=django.db.models.deletion.DO_NOTHING, to='ingest.Bulk'),
            preserve_default=False,
        )
    ]
