##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import os
import hashlib

from django.core.cache import cache
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.utils.timezone import now
from toolware.utils.generic import get_uuid
from slugify import slugify


def uploadto_user_photo(instance, filename):
    """ Given an image filename, returns a relative path to the image for a member """

    path = 'images/members'
    base, ext = os.path.splitext(filename.lower())
    base = get_uuid(12, 4)
    date = now().strftime("%Y/%m/%d")

    upload_to = '{}/photos/{}/{}{}'.format(path, date, slugify(base), ext)
    return upload_to


def get_user_permissions(user):
    """ Returns a list of permission `codename` for `user` """
    if not user or not user.is_active or user.is_anonymous:
        return []

    if user.is_superuser:
        return Permission.objects.all().values_list('codename', flat=True)

    user_perms = user.user_permissions.all().values_list('codename', flat=True)
    group_perms = Permission.objects.filter(group__user=user).values_list('codename', flat=True)

    permissions = list(user_perms) + list(set(group_perms) - set(user_perms))
    return permissions


def has_all_permissions(user, permissions):
    """ Return `True` only if the user has all the permissions """

    for perm in permissions:
        if not user.has_perm(perm):
            return False
    return True


def has_any_permissions(user, permissions):
    """ Retuns `True` if the user has any of the permissions """

    for perm in permissions:
        if user.has_perm(perm):
            return True
    return False


def calculate_user_checksum(user, refresh=False):
    """ Calculate checksum for user """

    cache_key = 'user-checksome-{}'.format(user.email)
    if not refresh:
        checksum = cache.get(cache_key)
        if checksum:
            return checksum

    permissions = ' '.join(sorted(user.get_all_permissions()))
    sorted_refs = [(
        'permissions',
        'password',
        'email',
        'is_active',
        'fullname',
        'language',
        'status',
        'is_superuser',
        'is_staff',
        'avatar',
    )]
    sorted_refs += [(
        permissions,
        user.password,
        user.email,
        user.is_active,
        user.get_full_name(),
        user.language,
        user.status,
        user.is_superuser,
        user.is_staff,
        user.avatar
    )]
    checksum_input = str(sorted_refs).encode('utf-8')
    checksum = hashlib.sha1(checksum_input).hexdigest()
    cache.set(cache_key, checksum)
    return checksum
