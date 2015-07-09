# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='volume_uri',
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='extra_data',
            field=jsonfield.fields.JSONField(default=b'{}'),
        ),
    ]
