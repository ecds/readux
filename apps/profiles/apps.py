##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ProfilesConfig(AppConfig):
    """
    Configuration entry point for the profiles app
    """

    # Translators: admin
    name = "profiles"
    # Translators: admin
    verbose_name = "User Profile"

    def ready(self):
        """
        App is imported and ready, so bootstrap it.
        """
        from . import receivers
