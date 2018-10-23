##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import logging

from django.conf import settings
from django.utils import six
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from rest_framework import serializers

from ..utils.common import get_url_name

log = logging.getLogger(__name__)
User = get_user_model()
