##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.utils.translation import ugettext as _


class AuthenticationError(Exception):
    status_code = 401

    # Translators: auth:i18n
    message = _('ERROR.INCORRECT.CREDENTIALS')

    def __init__(self, message=None):
        if message:
            self.message = message

    def __str__(self):
        return self.message


class AuthorizationError(Exception):
    status_code = 403

    # Translators: auth:i18n
    message = _('ERROR.INCORRECT.PERMISSIONS')

    def __init__(self, message=None):
        if message:
            self.message = message

    def __str__(self):
        return self.message


class RequestError(Exception):
    status_code = 400

    # Translators: auth:i18n
    message = _('ERROR.BAD_REQUEST')

    def __init__(self, message=None):
        if message:
            self.message = message

    def __str__(self):
        return self.message
