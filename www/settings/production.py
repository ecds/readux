##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import sys
import os.path

from .base.defaults import *

DEBUG = False

# We are running the production server
ALLOWED_FLAVOR = 'PRODUCTION'

# Prevent code running on non-development servers
if DEPLOYMENT_FLAVOR != ALLOWED_FLAVOR:
    warnings.warn('Invalid Django server type. {}'.format(DEPLOYMENT_FLAVOR))
    sys.exit(0)

# Ensure the settings point to development assets
if CONFIGURATION_FLAVOR != ALLOWED_FLAVOR:
    warnings.warn('Invalid Django settings file. {}'.format(CONFIGURATION_FLAVOR))
    sys.exit(0)

# Directory for logging
LOG_TO_DIR = False
if LOG_TO_DIR:
    LOG_DIR = os.path.abspath(os.path.join(BASE_DIR, '../../log'))

    LOGGING['handlers'].update({
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, '{}.log'.format(SITE_DOMAIN)),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'simple',
        }
    })

    LOGGING['loggers'].update({
        'sitewide': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        }
    })
