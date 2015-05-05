"""
Django settings for readux project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django_image_tools',
    'social.apps.django_app.default',
    'eulfedora',
    # emory_ldap included to migrate back to auth.User;
    # should be removed in the next version
    'eullocal.django.emory_ldap',
    'eultheme',
    'widget_tweaks',
    'readux.annotations',
    'readux.books',
    'readux.collection',
    'readux.dyndzi',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware'
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # django default context processors
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    # additional context processors
    "django.core.context_processors.request",  # always include request in render context
    "django.core.context_processors.static",
    # social auth support
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
    "eultheme.context_processors.template_settings",
    "eultheme.context_processors.site_path",
    "readux.context_extras",  # include app version, backend names
    "readux.books.context_processors.book_search",  # book search form
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'templates'),
]

SITE_ID = 1

ROOT_URLCONF = 'readux.urls'

WSGI_APPLICATION = 'readux.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'static')


# Additional locations of static files
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'sitemedia'),
]

# base url for user-uploaded content
MEDIA_URL = '/media/'

# supported mechanisms for login
AUTHENTICATION_BACKENDS = (
    # additional social-auth backends could be configured here;
    # they will need keys in localsettings and possibly display names
    # added to the dict in readux/__init__.py
    'social.backends.twitter.TwitterOAuth',
    'social.backends.google.GoogleOAuth2',
    'social.backends.github.GithubOAuth2',
    'social.backends.facebook.FacebookOAuth2',
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_ldap.backend.LDAPBackend',
)

SOCIAL_AUTH_USER_MODEL = 'auth.User'

LOGIN_REDIRECT_URL = '/'

# path to local copy of solr schema
SOLR_SCHEMA = os.path.join(BASE_DIR, 'deploy', 'solr', 'schema.xml')

try:
    from localsettings import *
except ImportError:
    import sys
    print >> sys.stderr, '''Settings not defined.  Please configure a version of
    localsettings.py for this site.  See localsettings.py.dist for an example.'''
    del sys


django_nose = None
try:
    # NOTE: errors if DATABASES is not configured (in some cases),
    # so this must be done after importing localsettings
    import django_nose
except ImportError:
    pass

# - only if django_nose is installed, so it is only required for development
if django_nose is not None:
    INSTALLED_APPS.append('django_nose')
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    NOSE_PLUGINS = [
        'eulfedora.testutil.EulfedoraSetUp',
        # ...
    ]
    NOSE_ARGS = ['--with-eulfedorasetup']

