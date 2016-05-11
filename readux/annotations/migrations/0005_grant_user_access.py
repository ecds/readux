# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm


def grant_user_access(apps, schema_editor):
    # updating to user django-guardian for object-specific permissions;
    # run grant user access method to ensure users continue to be able
    # to update and manage their own annotations.

    Annotation = apps.get_model("annotations", "Annotation")
    User = get_user_model()
    user_permissions = ['view_annotation', 'change_annotation',
                        'delete_annotation', 'admin_annotation']
    for note in Annotation.objects.all():
        # equivalent to Annotation grant_user_access method,
        # but that is not available within a migration
        if note.user is not None:
            # NOTE: guardian is particular about user/group models,
            # and doesn't seem to like the migration note.user here
            # retrieve the user object directly and use that
            user = User.objects.get(pk=note.user.pk)
            for perm in user_permissions:
                assign_perm(perm, user, note)


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0004_clean_extra_data'),
    ]

    operations = [
        migrations.RunPython(grant_user_access,
                             reverse_code=migrations.RunPython.noop),
    ]
