# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('annotations', '0002_add_volume_uri'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnnotationGroup',
            fields=[
                ('group_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='auth.Group')),
                ('notes', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            bases=('auth.group',),
        ),
        migrations.AlterModelOptions(
            name='annotation',
            options={'permissions': (('view_annotation', 'View annotation'),)},
        ),
    ]
