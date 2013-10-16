from django.conf import settings
import constants

# Automatically create a superuser based on the following credentials (if present)
USERWARE_SUPERUSER_EMAIL = getattr(settings, 'USERWARE_SUPERUSER_EMAIL', '')
USERWARE_SUPERUSER_USERNAME = getattr(settings, 'USERWARE_SUPERUSER_USERNAME', '')
USERWARE_SUPERUSER_PASSWORD = getattr(settings, 'USERWARE_SUPERUSER_PASSWORD', '')


USERWARE_PASSWORD_MIN_LENGTH = getattr(settings, 'USERWARE_PASSWORD_MIN_LENGTH', 6)

USERWARE_USERNAME_MIN_LENGTH = getattr(settings, 'USERWARE_USERNAME_MIN_LENGTH', 2)
USERWARE_RESERVED_USERNAMES = getattr(settings, 'USERWARE_RESERVED_USERNAMES', constants.USERWARE_RESERVED_USERNAMES)

LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')
LOGOUT_REDIRECT_URL = getattr(settings, 'LOGOUT_REDIRECT_URL', '/')

USERWARE_TEMPLATE_TAGS_AUTO_LOAD = getattr(settings, 'USERWARE_TEMPLATE_TAGS_AUTO_LOAD', True)

USERWARE_SUPERUSER_ID = getattr(settings, 'USERWARE_SUPERUSER_ID', 139)


