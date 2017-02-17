# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.core.management import call_command


def load_fixture(apps, schema_editor):
    'Load default version of editable site index page.'
    call_command('loaddata', 'site_index')

def unload_fixture(apps, schema_editor):
    'Remove default edtabile version of site index page.'
    Page = apps.get_model("page", "Page")
    Page.objects.filter(override_url='/').delete()


class Migration(migrations.Migration):

    dependencies = [
        # might depend on feincms pages migrations?
    ]

    operations = [
        migrations.RunPython(load_fixture, reverse_code=unload_fixture, atomic=False)
    ]
