##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from toolware.utils.query import get_or_create_unique

from . import defaults as defs


def drop_groups():
    """ Remove all groups """
    Group.objects.all().delete()


def add_group(name, permissions=None):
    """ Create a group if doesn't exist, and add permissions to it """
    defaults, unique_fields = {'name': name}, ['name']
    group, created = get_or_create_unique(Group, defaults, unique_fields)

    for perm in permissions:
        existing_perm = Permission.objects.get(codename=perm)
        group.permissions.add(existing_perm)
    return group


def load_groups():
    """ Load groups """
    drop_groups()

    for group_name, group_value in defs.AVAILABLE_GROUPS.items():
        for app_name, app_value in group_value.items():
            for model_name, model_value in app_value.items():
                permissions = ['{}_{}'.format(perm, model_name) for perm in model_value]
                add_group(group_name, permissions)
