##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.db.models.signals import post_migrate
from django.apps import AppConfig
from django.conf import settings

def post_migrate_callback(sender, **kwargs):
    from .group.utils import load_groups
    load_groups()


class SitewareConfig(AppConfig):
    """
    Configuration entry point for the sitewide app
    """
    
    # Translators: admin
    name = "sitewide"
    # Translators: admin
    verbose_name = "Sitewide config app"

    def ready(self):
        post_migrate.connect(post_migrate_callback, sender=self)
