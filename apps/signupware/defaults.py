from django.conf import settings

SIGNUPWARE_SPAMWARE_INSTALLED = True if 'spamware' in settings.INSTALLED_APPS else False

SIGNUPWARE_VERIFY_EMAIL = getattr(settings, 'SIGNUPWARE_VERIFY_EMAIL', False)

LOGIN_URL = getattr(settings, 'LOGIN_URL', '/')
LOGIN_REDIRECT_URL = getattr(settings, 'LOGIN_REDIRECT_URL', '/')




