##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.db import models
from django.utils import timezone


class Sitewide(models.Model):
    """
    Sitewide related data
    """

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    unique_id = models.TextField()

    class Meta:
        # Translators: admin
        verbose_name = 'Sitewide'

        permissions = (
            # ('add_sitewide', 'Can add new sitewide'),
            # ('change_sitewide', 'Can change all data on any sitewide'),
            # ('delete_sitewide', 'Can delete any non-superuser sitewide'),
            ('admin_sitewide', 'access to the admin menu'),
            ('staff_sitewide', 'access to limited admin menu'),
        )
