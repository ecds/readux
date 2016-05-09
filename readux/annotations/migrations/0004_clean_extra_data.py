# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def clean_extra_data(apps, schema_editor):
    Annotation = apps.get_model("annotations", "Annotation")

    # error in update logic was resulting in internal fields
    # being duplicated in the extra data json field; remove them
    non_extra_fields = ['id', 'updated', 'created', 'user']
    for note in Annotation.objects.all():
        changed = False
        for field in non_extra_fields:
            if field in note.extra_data:
                del note.extra_data[field]
                changed = True

        # only save if change, since it affects modification date
        if changed:
            note.save()


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0003_annotation_group_and_permissions'),
    ]

    operations = [
        migrations.RunPython(clean_extra_data,
                             reverse_code=migrations.RunPython.noop),
    ]
