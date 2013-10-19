import os
from os import path
import re
import warnings
import sys
import json


# Server Root (all sites reside here)
#######################################
SERVER_ROOT_DIR = '/srv/www/'

# Domain / Project Name
#######################################
PROJ_NAME = 'Djangoware'
PROJ_DOMAIN = PROJ_NAME.lower()+'.org'
ALLOWED_HOSTS = [PROJ_DOMAIN,]

# Path to the main project containing PROJ_SITE_NAME
#######################################
PROJ_ROOT_DIR = path.abspath(path.join(path.dirname(__file__), '../../'))

# Path to the template directory(ies)
#######################################
TEMPLATE_DIRS = ['%s' % path.abspath(path.join(PROJ_ROOT_DIR, 'www', 'templates')),]

# Assets configs
#######################################
ASSETS_DIR =  path.abspath(path.join(PROJ_ROOT_DIR, 'asset'))
# Static directories to look at during the development
STATICFILES_DIRS = ['%s' % path.abspath(path.join(ASSETS_DIR, 'static')),]
# Path to the static directory (collectstatic copies static assets to for deployment)
STATIC_ROOT = path.abspath(path.join(ASSETS_DIR, 'collect'))
# Path to the dynamic directory for user uploaded data
MEDIA_ROOT = path.abspath(path.join(ASSETS_DIR, 'upload'))
# URL to the static assets
STATIC_URL = '/s/'
# URL to the user uploaded assets
MEDIA_URL = '/m/'


# Path to our secret file outside out project directory (not under this version control)
#######################################
SECRET_FILE = path.abspath(path.join(SERVER_ROOT_DIR, 'seekrets/{}/settings/seekrets.json'.format(PROJ_DOMAIN)))
if not os.path.exists(SECRET_FILE):
    warnings.warn("Secret file not found")
    sys.exit(0)
else:
    SEEKRETS = json.load(open(SECRET_FILE, 'r'))

# Load up secret files
#######################################
try:
    SECRET_KEY = str(SEEKRETS['secret_key'])
    DB_NAME = str(SEEKRETS['database_name'])
    DB_USER = str(SEEKRETS['database_user'])
    DB_PASS = str(SEEKRETS['database_pass'])
    
except:
    warnings.warn("Failed to load secrets")
    sys.exit(0)

USERWARE_SUPERUSER_USERNAME = str(SEEKRETS.get('superuser_username', ''))
USERWARE_SUPERUSER_EMAIL = str(SEEKRETS.get('superuser_email', ''))
USERWARE_SUPERUSER_PASSWORD = str(SEEKRETS.get('superuser_password', ''))
SITE_ADMIN_URL_PATH = str(SEEKRETS.get('admin_url_path', 'admin'))
POSTMARK_API_KEY = str(SEEKRETS.get('postmark_api_key', ''))

# Site Specifics
#######################################
LANGUAGE_CODE = 'en-us'
USE_I18N = False
USE_L10N = False
USE_THOUSAND_SEPARATOR = True
SITE_PROTOCOL = 'http'
ROOT_URLCONF = 'urls'
SITE_ID = 1
DEFAULT_COUNTRY = 'Canada'
TIME_ZONE = 'Canada/Eastern'
USE_TZ = True


# Mail Server
#######################################
EMAIL_HOST = "localhost"
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = '%s <support@%s>' % (PROJ_NAME, PROJ_DOMAIN)
EMAIL_SUBJECT_PREFIX = '[%s]' % PROJ_NAME
# Server error messges are sent by this email
SERVER_EMAIL = 'support@{}'.format(PROJ_DOMAIN)
# System erros (5XX) are sent to this address
ADMINS = (('Server Admin', 'support@{}'.format(PROJ_DOMAIN)),)
# Page Not Found (404) errors are sent to this address
MANAGERS = (('Site Admin', 'support@{}'.format(PROJ_DOMAIN)),)

# Cache Related Stuff
#######################################
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

# Database
#######################################
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path.abspath(path.join(PROJ_ROOT_DIR, PROJ_NAME.lower()+'_db')),
    }
}

######################################
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_DOMAIN = '.' + PROJ_DOMAIN
SESSION_COOKIE_HTTPONLY = True
SESSION_IDLE_TIMEOUT = 60 * 60 * 24
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Broken Link emails: Ignore few request by robots
#######################################
SEND_BROKEN_LINK_EMAILS = False
if SEND_BROKEN_LINK_EMAILS:
    IGNORABLE_404_URLS = (
        re.compile(r'\.(php|cgi|asp|css|js|aspx)'),
        re.compile(r'^/phpmyadmin/'),
        re.compile(r'^/beta/'),
        re.compile(r'^/favicon\.ico$'),
        re.compile(r'^/robots\.txt$'),
    )


# Basic logging
#######################################
SITE_LOG_FILE = path.abspath(path.join(SERVER_ROOT_DIR, '{}/log/{}.log'.format(PROJ_DOMAIN, PROJ_DOMAIN)))
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {"format": "[%(name)s] %(levelname)s: %(message)s"},
        "full": {"format": "%(asctime)s [%(name)s] %(levelname)s: %(message)s"}
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    "handlers": {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "logfile": {
            "formatter": "full",
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": SITE_LOG_FILE,
            "when": "D",
            "interval": 7,
            "backupCount": 5,
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
    }
}

# Template Tags we need to load up automatically
################################################
AUTO_LOAD_TEMPLATE_TAGS_LIST = [
    # django tags
    'django.templatetags.cache',
    'django.templatetags.future',
    'django.templatetags.i18n',
    'django.templatetags.l10n',
    'django.templatetags.static',
    'django.contrib.humanize.templatetags.humanize',
]


