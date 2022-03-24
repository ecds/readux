# Generated by Django 3.2.12 on 2022-03-22 19:17

import apps.utils.noid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0042_auto_20220316_1612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manifest',
            name='pid',
            field=models.CharField(default=apps.utils.noid.encode_noid, help_text="Unique ID. Do not use _'s or spaces in the pid.", max_length=255),
        ),
    ]