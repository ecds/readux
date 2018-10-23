##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

DEFAULT_FILE_STORAGE = getattr(settings, 'DEFAULT_FILE_STORAGE')

USER_STATUS_NEW = 'new'
USER_STATUS_ACTIVE = 'active'
USER_STATUS_OVERDUE = 'overdue'
USER_STATUS_BANNED = 'banned'
USER_STATUS_SUSPENDED = 'suspended'

USER_STATUS_CHOICES = [
    # Translators: portal
    (USER_STATUS_NEW, _('USER.STATUS.NEW')),
    # Translators: portal
    (USER_STATUS_OVERDUE, _('USER.STATUS.OVERDUE')),
    # Translators: portal
    (USER_STATUS_ACTIVE, _('USER.STATUS.ACTIVE')),
    # Translators: portal
    (USER_STATUS_BANNED, _('USER.STATUS.BANNED')),
    # Translators: portal
    (USER_STATUS_SUSPENDED, _('USER.STATUS.SUSPENDED')),
]

USER_STATUS_DEFAULT = USER_STATUS_NEW
USER_DEFAULT_LANGUAGE = 'en'
