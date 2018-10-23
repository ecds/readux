##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.contrib.auth import get_user_model
from django.db.models import signals
from django.apps import AppConfig as DjangoAppConfig

from .utils.common import get_api_namespace

APP_NAMESPACE = get_api_namespace(__name__)


class AppConfig(DjangoAppConfig):
    """
    Configuration entry point for the api version one app
    """
    label = name = APP_NAMESPACE
    verbose_name = APP_NAMESPACE + 'application'

    def ready(self):
        pass
