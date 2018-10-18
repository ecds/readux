##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###


import os
import sys
import json
import warnings
import hmac
from hashlib import sha1

# Debugging flag during development - Set False on production
#######################################
DEBUG = False

# Testing flag during CI - Set False on production
#######################################
TESTING = False

# Notify the Manifest enabled backend storage to create a unique manifest file.
#######################################
MANIFEST_STATIC_FILE_VERSION = '0.0.1'

# Base directory for our project
#######################################
BASE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))

# Path to our secret file apart from our source code directories.
#######################################
SECRET_FILE = os.path.abspath(os.path.join(BASE_DIR, "seekrets.json"))
if not os.path.isfile(SECRET_FILE):
    warnings.warn('Missing secret file!')
    sys.exit(0)
else:
    CONFIG_DATA = json.load(open(SECRET_FILE, 'r'))

# Flavor verification - the code, config & environment must all have the same flavor
#######################################
# Code flavors
ALLOWED_FLAVOR = 'DEVELOPMENT'
# Config flavor
CONFIGURATION_FLAVOR = CONFIG_DATA.get('CONFIGURATION_FLAVOR', ALLOWED_FLAVOR).upper()
# Environment flavor
DEPLOYMENT_FLAVOR = os.environ.get('DEPLOYMENT_FLAVOR', 'UNKNOWN').upper()

# Site Signature - Sensitive data for production servers
#######################################
SECRET_KEY = hmac.new(CONFIG_DATA['SECRET_KEY'].encode(), digestmod=sha1).hexdigest()

# Project Related Info
#######################################
SITE_NAME = CONFIG_DATA['SITE_NAME']
SITE_DOMAIN = CONFIG_DATA['SITE_DOMAIN']
SITE_AUTHOR = CONFIG_DATA.get('SITE_AUTHOR', SITE_DOMAIN)
SITE_PROTOCOL = CONFIG_DATA.get('SITE_PROTOCOL', 'http')
SITE_DESCRIPTION = CONFIG_DATA.get('SITE_DESCRIPTION', '')
SITE_API_DOMAIN = CONFIG_DATA.get('SITE_API_DOMAIN')
SITE_APP_DOMAIN = CONFIG_DATA.get('SITE_APP_DOMAIN')

SITE_SUPERUSER_EMAIL = CONFIG_DATA['SITE_SUPERUSER_EMAIL']
SITE_SUPERUSER_PASSWORD = CONFIG_DATA['SITE_SUPERUSER_PASSWORD']

# Authorized hosts - Sensitive list for production servers when Debug = False
#######################################
ALLOWED_HOSTS = CONFIG_DATA.get('ALLOWED_HOSTS', [])

# Trusted origins (Cross Site Request Forgery)
#######################################
CSRF_TRUSTED_ORIGINS = CONFIG_DATA.get('CSRF_TRUSTED_ORIGINS', [])

# Trusted origins (Cross Origin Resource Sharing)
#######################################
CORS_TRUSTED_ORIGINS = CONFIG_DATA.get('CORS_TRUSTED_ORIGINS', [])

# Database Related
#######################################
DEFAULT_DB_ENGINE = CONFIG_DATA.get('DEFAULT_DB_ENGINE', 'sqlite')
DEFAULT_DB_NAME = CONFIG_DATA['DEFAULT_DB_NAME']
DEFAULT_DB_USER = CONFIG_DATA['DEFAULT_DB_USER']
DEFAULT_DB_PASS = CONFIG_DATA['DEFAULT_DB_PASS']

# Cache Related
#######################################
DEFAULT_CACHE_ENGINE = CONFIG_DATA.get('DEFAULT_CACHE_ENGINE', 'memory')
DEFAULT_CACHE_ENGINE_PORT = CONFIG_DATA.get('DEFAULT_CACHE_ENGINE_PORT')

# Mail Server
#######################################
DEFAULT_FROM_EMAIL = CONFIG_DATA['DEFAULT_FROM_EMAIL']
# Server error messges are sent by this email
DEFAULT_SUPPORT_EMAL = CONFIG_DATA.get('DEFAULT_SUPPORT_EMAL', DEFAULT_FROM_EMAIL)
# System errors (5XX) are sent to this address
DEFAULT_ADMINS_EMAIL = CONFIG_DATA.get('DEFAULT_ADMINS_EMAIL', DEFAULT_FROM_EMAIL)
# Page Not Found (404) errors are sent to this address
DEFAULT_MANAGERS_EMAIL = CONFIG_DATA.get('DEFAULT_MANAGERS_EMAIL', DEFAULT_FROM_EMAIL)

# AWS Related
#######################################
AWS_ACCESS_KEY_ID = CONFIG_DATA.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = CONFIG_DATA.get('AWS_SECRET')
AWS_MEDIA_BUCKET_NAME = CONFIG_DATA.get('AWS_MEDIA_BUCKET_NAME', '')
AWS_MEDIA_BUCKET_CNAME = CONFIG_DATA.get('AWS_MEDIA_BUCKET_CNAME', '')
AWS_STATIC_BUCKET_NAME = CONFIG_DATA.get('AWS_STATIC_BUCKET_NAME', '')
AWS_STATIC_BUCKET_CNAME = CONFIG_DATA.get('AWS_STATIC_BUCKET_CNAME', '')

# Google analytics
#######################################
GOOGLE_ANALYTICS_KEY = CONFIG_DATA.get('GOOGLE_ANALYTICS_KEY')
