from deploy import *

# Debug info
#######################################
DEBUG = True
TEMPLATE_DEBUG = DEBUG

DEBUG_USE_SQLITE3 = True
DEBUG_SKIP_CSRF_MIDDLEWARE = True
DEBUG_SKIP_CLICKJACKING_MIDDLEWARE = True
DEBUG_ENABLE_TOOLBAR = True
DEBUG_ENABLE_COMMAND_EXTENSSION = True
DEBUG_LOGGING_ONLY = True
DEBUG_CONSOLE_LOG_LEVEL = 'ERROR'
DEBUG_ENABLE_LOCAL_CACHE_BACKEND = False
DEV_IP_ADDRESS = '192.168.211.130'

# quick test of project with sqlite3
#######################################
if DEBUG_USE_SQLITE3:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': path.abspath(path.join(PROJ_ROOT_DIR, PROJ_NAME.lower()+'_db')),
        }
    }

# remove CSRF if flag is set
#######################################
if DEBUG_SKIP_CSRF_MIDDLEWARE:
    del MIDDLEWARE_CLASSES[MIDDLEWARE_CLASSES.index('django.middleware.csrf.CsrfViewMiddleware')]

# remove ClickJacking if flag is set
#######################################
if DEBUG_SKIP_CLICKJACKING_MIDDLEWARE:
    del MIDDLEWARE_CLASSES[MIDDLEWARE_CLASSES.index('django.middleware.clickjacking.XFrameOptionsMiddleware')]

# debug toolbar
#######################################
if DEBUG_ENABLE_TOOLBAR:
    # bless debug toolbar with development (ONLY) IP(s)
    INTERNAL_IPS = ['127.0.0.1', DEV_IP_ADDRESS]
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        # order matters, so insert the debug toolbar app right after the common middleware
        common_index = MIDDLEWARE_CLASSES.index('django.middleware.common.CommonMiddleware')
        MIDDLEWARE_CLASSES.insert(common_index+1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INSTALLED_APPS.append('debug_toolbar')
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda req: True,
            'INTERCEPT_REDIRECTS': False,
        }

# debug command extesions (lot of goodies)
#######################################
if DEBUG_ENABLE_COMMAND_EXTENSSION:
    try:
        import django_extensions
    except ImportError:
        pass
    else:
        INSTALLED_APPS.append('django_extensions')

# allow test apps in debug mode
#######################################
INSTALLED_APPS.append('testware')

# use dev server instead of the builtin dev server
#######################################
INSTALLED_APPS.append('devserver')
DEVSERVER_DEFAULT_ADDR = DEV_IP_ADDRESS
DEVSERVER_DEFAULT_PORT = 8080

# debug logging
#######################################
if DEBUG_LOGGING_ONLY:
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
                'level': 'DEBUG',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            },
            "console": {
                "level": "{}".format(DEBUG_CONSOLE_LOG_LEVEL),
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "loggers": {
            "django.request": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
        }
    }

    # Site loggin
    #######################################
    non_core_app_index_start = INSTALLED_APPS.index('postware')
    for index, app in enumerate(INSTALLED_APPS, start=0):
        if index == 0 or index >= non_core_app_index_start:
            LOGGING['loggers'].update({
                app: {
                    "handlers": ['console'],
                    "level": "DEBUG",
                }
            })


# cache backend during debugging
#######################################
if DEBUG_ENABLE_LOCAL_CACHE_BACKEND:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake'
        }
    }

# Don't care about this in debug mode (allows login via admin in debug when session in cookies used)
#######################################
SESSION_COOKIE_DOMAIN = ''

# Assets overright
#######################################
# URL to the static assets
STATIC_URL = '/s/'
# URL to the user uploaded assets
MEDIA_URL = '/m/'

# Falls on development IP from finalize.sites
#######################################
SITE_OBJECTS_INFO_DICT = {
    '1': {
        'name': PROJ_NAME,
        'domain': PROJ_DOMAIN
    },
    '2':{
        'name': 'Development',  # dev  (optional)
        'domain': '{}:8080'.format(DEV_IP_ADDRESS)
    },
}
SITE_ID = 2
SITE_PROTOCOL = 'http'

# Admin User Overwrite
#######################################
USERWARE_SUPERUSER_PASSWORD = 'hello'

# Always load a fresh copy of assets during the development
#######################################
FRESHLY_ASSETS_ALWAYS_FRESH = True




