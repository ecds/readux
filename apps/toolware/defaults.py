from django.conf import settings

TOOLWARE_DEBUG = getattr(settings, 'DEBUG', False)

TOOLWARE_TEMPLATE_TAGS_AUTO_LOAD = getattr(settings, 'TOOLWARE_TEMPLATE_TAGS_AUTO_LOAD', True)

LOGIN_URL = getattr(settings, 'LOGIN_URL', '/')
LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')

