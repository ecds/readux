##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import sys

from .base.defaults import *

DEBUG = False

# We are running the staging server
ALLOWED_FLAVOR = 'STAGING'

# Prevent code running on non-development servers
if DEPLOYMENT_FLAVOR != ALLOWED_FLAVOR:
    warnings.warn('Invalid Django server type. {}'.format(DEPLOYMENT_FLAVOR))
    sys.exit(0)

# Ensure the settings point to development assets
if CONFIGURATION_FLAVOR != ALLOWED_FLAVOR:
    warnings.warn('Invalid Django settings file. {}'.format(CONFIGURATION_FLAVOR))
    sys.exit(0)
