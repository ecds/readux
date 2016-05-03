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
    'eultheme',
    'downtime',
    'widget_tweaks',
    'feincms',
    'mptt',
    'feincms.module.page',
    'feincms.module.medialibrary',
    'readux.annotations',
    'readux.accounts',
    'readux.books',
    'readux.collection',
    'readux.pages',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'eultheme.middleware.DownpageMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'readux.accounts.middleware.LocalSocialAuthExceptionMiddleware'
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # django default context processors
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    # additional context processors
    'eultheme.context_processors.template_settings',
    "django.core.context_processors.request",  # always include request in render context
    "django.core.context_processors.static",
    # social auth support
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
    "eultheme.context_processors.template_settings",
    "eultheme.context_processors.site_path",
    "eultheme.context_processors.downtime_context",
    "readux.context_extras",  # include app version, backend names
    "readux.books.context_processors.book_search",  # book search form
    "readux.pages.context_processors.default_page",
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

LARGE_PDF_THRESHOLD=''

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
    # The app will use the following backends prioritized by list order.
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.github.GithubOAuth2',
    'social.backends.google.GoogleOAuth2',
    'social.backends.twitter.TwitterOAuth',
    'social.backends.zotero.ZoteroOAuth',
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = '/'

# additional github permissions, for annotated volume export to github
SOCIAL_AUTH_GITHUB_SCOPE = ['public_repo']

# path to local copy of solr schema
SOLR_SCHEMA = os.path.join(BASE_DIR, 'deploy', 'solr', 'schema.xml')


# exempted paths for downtime; exempts any urls starting with these strings
DOWNTIME_EXEMPT_PATHS = (
    '/admin',
    '/indexdata',
    '/sitemap'
)
DOWNTIME_EXEMPT_EXACT_URLS = (
    '/',
)

FEINCMS_RICHTEXT_INIT_CONTEXT = {
    'TINYMCE_JS_URL': '//tinymce.cachefly.net/4.2/tinymce.min.js'
}

GIT_AUTHOR_EMAIL = 'readux.emory@gmail.com'
GIT_AUTHOR_NAME = 'readux'


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

# enable django-debug-toolbar when available & in debug/dev modes
if DEBUG or DEV_ENV:
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
    except ImportError:
        pass

# configure: default toolbars + existdb query panel
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'eulfedora.debug_panel.FedoraPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    # 'debug_toolbar.panels.profiling.ProfilingPanel',
]
