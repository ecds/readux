from django.conf import settings

TOOLWARE_DEBUG = getattr(settings, 'DEBUG', False)

TOOLWARE_INCLUDE_TEMPLATE_TAGS = getattr(settings, 'TOOLWARE_INCLUDE_TEMPLATE_TAGS', True)

LOGIN_URL = getattr(settings, 'LOGIN_URL', '/')
LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')

