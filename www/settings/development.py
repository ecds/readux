##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###


import os

from .base.defaults import *

ALLOWED_HOSTS = ["*"]
SITE_SUPERUSER_PASSWORD = 'hello'
SESSION_COOKIE_SECURE = False

# Development flag for quickly enable/disable debugging options
DEBUG = True
DEBUG_TEMPLATE = DEBUG
DEV_IP_ADDRESS = '127.0.0.1'
DEBUG_ENABLE_TOOLBAR = True
DEBUG_ENABLE_COMMAND_EXTENSION = True
DEBUG_AWS = False
DEBUG_USE_SQLITE3 = True
DEBUG_FRONT_END = True  # If True, then don't force-logout front-end client on auth errors
POSTMARK_TEST_MODE = False
ADMIN_DOCS_ENABLED = True
GRAPHQL_DEBUG = True

# Prevent code running on non-development servers
if DEPLOYMENT_FLAVOR != ALLOWED_FLAVOR:
    warnings.warn('Invalid Django server type. {}'.format(DEPLOYMENT_FLAVOR))
    sys.exit(0)

# Ensure the settings point to development assets
if CONFIGURATION_FLAVOR != ALLOWED_FLAVOR:
    warnings.warn('Invalid Django settings file. {}'.format(CONFIGURATION_FLAVOR))
    sys.exit(0)

# Enable command extensions on per-need basis
if DEBUG_ENABLE_COMMAND_EXTENSION:
    INSTALLED_APPS = INSTALLED_APPS + [
        'django_extensions',
    ]
    os.environ['WERKZEUG_DEBUG_PIN'] = 'off'

# Assets overwrite
#######################################
if DEBUG_AWS:
    REMOTE_STORAGE_ENABLED = True
    SITE_PROTOCOL = 'http'
    AWS_S3_URL_PROTOCOL = SITE_PROTOCOL + ':'
    AWS_MEDIA_BUCKET_NAME = AWS_MEDIA_BUCKET_NAME
    AWS_MEDIA_CDN = AWS_MEDIA_BUCKET_CNAME
    AWS_STATIC_BUCKET_NAME = AWS_STATIC_BUCKET_NAME
    AWS_STATIC_CDN = AWS_STATIC_BUCKET_CNAME
else:
    REMOTE_STORAGE_ENABLED = False
    DEFAULT_FILE_STORAGE = 'sitewide.storage.backend.MediaFilesStorage'
    STATICFILES_STORAGE = 'sitewide.storage.backend.StaticFilesStorage'
    SITE_PROTOCOL = 'http'

# Debug Toolbar
#######################################
if DEBUG and DEBUG_ENABLE_TOOLBAR:
    INTERNAL_IPS = DEV_IP_ADDRESS
    try:
        import debug_toolbar
    except ImportError:
        warnings.warn('Debug toolbar is not installed. (pip install django-debug-toolbar)')
    else:
        INSTALLED_APPS = INSTALLED_APPS + [
            'debug_toolbar',
        ]
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda req: True,
            'INTERCEPT_REDIRECTS': False,
        }
        # order matters, so insert the debug toolbar app right after the common middleware
        # https://github.com/django-debug-toolbar/django-debug-toolbar/issues/853
        debug_toolbar_index = MIDDLEWARE.index('django.middleware.common.CommonMiddleware') + 1
        MIDDLEWARE.insert(debug_toolbar_index, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Falls on development IP from finalize.sites
#######################################
SITE_OBJECTS_INFO_DICT['2'] = {
    'name': SITE_NAME + ' - Development',
    'domain': '{}:8181'.format(DEV_IP_ADDRESS)
}
SITE_ID = 2

# Site logger level
#######################################
LOGGING['loggers'].update({
    'django': {
        'handlers': ['console'],
    },
    'django.request': {
        'handlers': ['mail_admins'],
        'level': 'ERROR',
        'propagate': False,
    },
    'py.warnings': {
        'handlers': ['console'],
    },
    'sitewide': {
        'handlers': ['console'],
        'level': 'INFO',
        'propagate': False,
    },
    'django.db': {
        'handlers': ['console'],
        'level': 'INFO',
        'propagate': False,
    },
})


# Development Database Choice
#######################################
if DEBUG_USE_SQLITE3:
    DATABASES['default'] = DATABASES_OPTIONS['sqlite']
