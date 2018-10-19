##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

import os
import sys

from .config import *

# Assets configs
#######################################
ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, 'assets'))
# Static directories to look at during the development
STATICFILES_DIRS = ['{}'.format(os.path.abspath(os.path.join(ASSETS_DIR, 'static'))), ]
# Path to the static directory (collectstatic copies static assets to for deployment)
STATIC_ROOT = os.path.abspath(os.path.join(ASSETS_DIR, 'collect'))
# Path to the dynamic directory for user uploaded data
MEDIA_ROOT = os.path.abspath(os.path.join(ASSETS_DIR, 'upload'))
# URL to the static assets
STATIC_URL = '/s/'
# URL to the user uploaded assets
MEDIA_URL = '/m/'

# SITE PROTOCOL
#######################################
PROTOCOL = SITE_PROTOCOL

# Ordered list of installed applications
#######################################
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.postgres',
]

# Ordered list of installed middlewares
#######################################
MIDDLEWARE = [
    # Django middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # 3rd party middleware
    'sitewide.middleware.ProcessIpAddressMiddleware',
    'profiles.middleware.ProfileSignatureMiddleware'
]

# Configuration for templates
#######################################
TEMPLATES_BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, 'www', 'templates'))
TEMPLATES_SUB_DIRS = [
    'pages',        # Internal related pages
    'partials',     # Partials and layout related (not view ready)
    'server',       # HTTP server specific files (no context)
]
TEMPLATES_DIRS = [os.path.join(TEMPLATES_BASE_DIR, dir) for dir in TEMPLATES_SUB_DIRS]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATES_DIRS,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'finalware.context_processors.contextify',
            ],
            'builtins': [
                'django.templatetags.cache',
                'django.templatetags.i18n',
                'django.templatetags.l10n',
                'django.templatetags.tz',
                'django.contrib.humanize.templatetags.humanize',
                'django.contrib.staticfiles.templatetags.staticfiles',
                'sitewide.templatetags.languages',
            ],
            'loaders': (
                (
                    'django.template.loaders.cached.Loader',
                    (
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    )
                ),
            ),
        },
    },
]

# Start point of site URLS
#######################################
ROOT_URLCONF = 'sitewide.urls'

# Database configuration - basic
#######################################
DATABASES_OPTIONS = {
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, DEFAULT_DB_NAME),
    },
    'postgres': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DEFAULT_DB_NAME,
        'USER': DEFAULT_DB_USER,
        'PASSWORD': DEFAULT_DB_PASS,
    },
    'postgis': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': DEFAULT_DB_NAME,
        'USER': DEFAULT_DB_USER,
        'PASSWORD': DEFAULT_DB_PASS,
    },
    'mysql': {
        'ENGINE': 'mysql.connector.django',
        'NAME': DEFAULT_DB_NAME,
        'USER': DEFAULT_DB_USER,
        'PASSWORD': DEFAULT_DB_PASS,
        'OPTIONS': {
            'autocommit': True,
        },
    }
}
DATABASES = {'default': DATABASES_OPTIONS[DEFAULT_DB_ENGINE]}

# Cache Related
#######################################
CACHES_OPTIONS = {
    'dummy': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'memory': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    },
    'redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://cache-host:{}/1'.format(DEFAULT_CACHE_ENGINE_PORT or '6379'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_TIMEOUT': 2,
            'SOCKET_CONNECT_TIMEOUT': 2,
            'IGNORE_EXCEPTIONS': True,
            'TIMEOUT': 5,
        }
    },
    'memcached': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'cache-host:{}'.format(DEFAULT_CACHE_ENGINE_PORT or '11211'),
        'TIMEOUT': 180,
        'OPTIONS': {
            'MAX_ENTRIES': 4000,
            'CULL_FREQUENCY': 3,
        }
    },
}
CACHES = {'default': CACHES_OPTIONS[DEFAULT_CACHE_ENGINE]}

# Ordered list of password validations
#######################################
AUTH_PASSWORD_LENGTH = 6
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': AUTH_PASSWORD_LENGTH,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password Re/Set
#######################################
AUTH_PASSWORD_RESET_TIMEOUT_DAYS = 7

# Internationalization
#######################################
USE_I18N = True
LANGUAGE_CODE = 'en'
ENABLED_LANGUAGES = [
    'en',
]
LANGUAGES = (
    ('en', 'English'),
    ('fr', 'Français'),
    ('zh-hans', '中文 - 简体'),
    ('de', 'Deutsch'),
    ('es', 'Español'),
    ('he', 'עִברִית'),
)
# https://meta.wikimedia.org/wiki/Template:List_of_language_names_ordered_by_code
RTL_LANGUAGES = [
    'ar',
    'fa',
    'he',
    'arc',
    'dv',
    'ha',
    'khw',
    'ks',
    'ku',
    'ps',
    'ur',
    'yi'
]
LOCALE_PATHS = (
    os.path.abspath(os.path.join(BASE_DIR, 'locale')),
)

# Localization
#######################################
USE_L10N = True

# Timezone
#######################################
USE_TZ = True
TIME_ZONE = 'UTC'

# Basic logging
#######################################
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '[%(name)s] %(levelname)s: [%(lineno)d] %(message)s',
        },
        'full': {
            'format': '%(asctime)s [%(name)s] %(levelname)s: [%(lineno)d] %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': [
                'require_debug_false',
            ],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'full',
        },
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['mail_admins'],
            'level': 'CRITICAL',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Redirects
#######################################
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Authentication backends
#######################################
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Session
#######################################
# SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
# SESSION_COOKIE_NAME = '_session_uid_'
# SESSION_COOKIE_DOMAIN = '.' + '.'.join(SITE_DOMAIN.lower().split('.')[-2:])
# SESSION_COOKIE_AGE = 1209600 # (2 weeks, in seconds)
# SESSION_COOKIE_PATH = '/auth/'
# SESSION_COOKIE_SECURE = False
# SESSION_COOKIE_HTTPONLY = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Custom User
#######################################
AUTH_USER_MODEL = 'profiles.Profile'

# Mail Server
#######################################
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
SERVER_EMAIL = DEFAULT_SUPPORT_EMAL
EMAIL_SUBJECT_PREFIX = '[{}]'.format(SITE_DOMAIN)
ADMINS = (('Server Admin', '{}'.format(DEFAULT_ADMINS_EMAIL)),)
MANAGERS = (('Site Admin', '{}'.format(DEFAULT_MANAGERS_EMAIL)),)

# Site objects auto config
#######################################
# site info (you need at least one site)
SITE_ID = 1
SITE_OBJECTS_INFO_DICT = {
    '1': {
        'name': SITE_NAME,
        'domain': SITE_DOMAIN,
    },
}

# Site installed apps
#######################################
AUTO_COMPLETE_APPS = ['dal', 'dal_select2']
INSTALLED_APPS = AUTO_COMPLETE_APPS + INSTALLED_APPS + [

    'corsheaders',
    'rest_framework',
    'profiles',
    'sitewide',
    'api_v1',

    # Must come last to finalize everything
    'finalware'
]

# Site logger level
#######################################
for app in INSTALLED_APPS:
    LOGGING['loggers'].update({
        app: {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        }
    })

# CORS headers
#######################################
if 'corsheaders' in INSTALLED_APPS:
    common_middleware_index = MIDDLEWARE.index('django.middleware.common.CommonMiddleware')
    MIDDLEWARE.insert(common_middleware_index - 1, 'corsheaders.middleware.CorsMiddleware')
    csrf_middleware_index = MIDDLEWARE.index('django.middleware.csrf.CsrfViewMiddleware')
    MIDDLEWARE.insert(csrf_middleware_index + 1, 'corsheaders.middleware.CorsPostCsrfMiddleware')
    CORS_ORIGIN_ALLOW_ALL = False
    CORS_URLS_REGEX = r'^/api/.*$|^/gql$'
    CORS_ORIGIN_WHITELIST = CORS_TRUSTED_ORIGINS
    CORS_EXPOSE_HEADERS = ['Profile-Signature']  # expose custom headers to browser

# Context-able data (finalware adds this list to context of all views)
#######################################
SITE_EXTRA_CONTEXT_DICT = {
    'GOOGLE_ANALYTICS_KEY': GOOGLE_ANALYTICS_KEY,
    'SITE_API_DOMAIN': SITE_API_DOMAIN,
    'SITE_APP_DOMAIN': SITE_APP_DOMAIN,
    'SITE_DESCRIPTION': SITE_DESCRIPTION,
}

# AWS Related
#######################################
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    REMOTE_STORAGE_ENABLED = True
    AWS_S3_SECURE_URLS = False
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_CALLING_FORMAT = 'boto.s3.connection.OrdinaryCallingFormat'
    AWS_HEADERS = {'Cache-Control': 'max-age=86400', }
    AWS_S3_URL_PROTOCOL = SITE_PROTOCOL + ':'
    AWS_MEDIA_BUCKET_NAME = AWS_MEDIA_BUCKET_NAME
    AWS_MEDIA_CDN = AWS_MEDIA_BUCKET_CNAME
    AWS_STATIC_BUCKET_NAME = AWS_STATIC_BUCKET_NAME
    AWS_STATIC_CDN = AWS_STATIC_BUCKET_CNAME
    AWS_MEDIA_FILE_STORAGE = 'sitewide.storage.backend.MediaFilesStorage'
    AWS_STATIC_FILES_STORAGE = 'sitewide.storage.backend.ManifestStaticFilesStorage'
    MEDIA_ASSETS_PREFIX = 'm'
    STATIC_ASSETS_PREFIX = 's'

    # Keep Django into loop regarding our AWS storage backends
    STATICFILES_STORAGE = AWS_STATIC_FILES_STORAGE
    DEFAULT_FILE_STORAGE = AWS_MEDIA_FILE_STORAGE

# Restful Framework
#######################################
REST_FRAMEWORK = {

    'PAGINATE_BY': 2,
    'MAX_PAGINATE_BY': 2,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',

    # allow dynamic pagination size `?page_size=xxx`.
    'PAGINATE_BY_PARAM': 'page_size',

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),

    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),

    'DEFAULT_MODEL_SERIALIZER_CLASS': (
        'rest_framework.serializers.HyperlinkedModelSerializer',
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoModelPermissions',
        'rest_framework.permissions.IsAdminUser',
    ),

    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.ScopedRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),

    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'burst': '60/min',
        'sustained': '1000/day',
        'profile_create': '20/day',
    }
}
