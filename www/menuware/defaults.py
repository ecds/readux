from django.conf import settings


# allow users to turn template tags autoload off
MENUWARE_AUTOLOAD_TEMPLATE_TAGS = getattr(settings, 'MENUWARE_AUTOLOAD_TEMPLATE_TAGS', True)

