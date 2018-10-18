##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(DjangoAppConfig):
    """
    Configuration entry point for the group app
    """
    
    # Translators: admin
    name = _("GROUP")
    # Translators: admin
    verbose_name = _("GROUP")

    def ready(self):
        """
        App is imported and ready, so bootstrap it.
        """
        pass
