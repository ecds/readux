# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.management import call_command


def load_fixture(apps, schema_editor):
    'Load image default sizes and filters.'
    call_command('loaddata', 'image_defaults', app_label='collection')

def unload_fixture(apps, schema_editor):
    'Remove image defualt sizes and filters.'
    ImageSize = apps.get_model("django_image_tools", "size")
    ImageSize.objects.filter(name__in=['thumbnail', 'banner']).delete()
    ImageFilter = apps.get_model("django_image_tools", "filter")
    ImageFilter.objects.filter(name__in=['blurred', 'greyscale']).delete()



class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_fixture, reverse_code=unload_fixture, atomic=False)
    ]
