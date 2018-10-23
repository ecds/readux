##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf import settings

MANIFEST_STATIC_FILE_VERSION = getattr(settings, 'MANIFEST_STATIC_FILE_VERSION', '0.0.1')
REMOTE_STORAGE_ENABLED = getattr(settings, 'REMOTE_STORAGE_ENABLED', False)
DEFAULT_LANGUAGE = getattr(settings, "DEFAULT_LANGUAGE", "en")
