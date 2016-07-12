import os
import sys
import json
import warnings
import hmac
from hashlib import sha1

# Debug flag - Sensitive flag for production servers
DEBUG = False

# Base directory for our project
#######################################
BASE_DIR = os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))

# Path to our secret file apart from our source code directories.
#######################################
SECRET_FILE = os.path.abspath(os.path.join(BASE_DIR, "seekrets.json"))
if not os.path.isfile(SECRET_FILE):
    warnings.warn('Secret file not found')
    sys.exit(0)
else:
    CONFIG_DATA = json.load(open(SECRET_FILE, 'r'))

# Site Signature - Sensitive data for production servers
SECRET_KEY = hmac.new(CONFIG_DATA['SECRET_KEY'].encode(), digestmod=sha1).hexdigest()

# Project name
PROJECT_NAME = str(CONFIG_DATA.get('PROJ_BASE', 'myproj'))

# Authorized hosts - Sensitive list for production servers when Debug = False
ALLOWED_HOSTS = []

# Ordered list of installed applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Ordered list of installed middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuration for templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Start point of site URLS
ROOT_URLCONF = 'siteware.urls'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '{}_db'.format(PROJECT_NAME)),
    }
}


# Ordered list of password validations
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
