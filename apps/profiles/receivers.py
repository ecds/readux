##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .utils import calculate_user_checksum

User = get_user_model()


@receiver(m2m_changed, sender=User.groups.through)
def user_group_changed(sender, **kwargs):
    action = kwargs.pop('action', None)
    if action in ['post_remove', 'post_add']:
        instance = kwargs.pop('instance', None)
        calculate_user_checksum(instance, refresh=True)


@receiver(m2m_changed, sender=User.user_permissions.through)
def user_permissions_changed(sender, **kwargs):
    action = kwargs.pop('action', None)
    if action in ['post_remove', 'post_add']:
        instance = kwargs.pop('instance', None)
        calculate_user_checksum(instance, refresh=True)


@receiver(post_save, sender=User)
def user_changed(sender, **kwargs):
    instance = kwargs.pop('instance', None)
    calculate_user_checksum(instance, refresh=True)
