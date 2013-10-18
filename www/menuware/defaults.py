from django.conf import settings


# By default, Menuware autoloads its template tags. Allow to turn autoload off via settings
MENUWARE_AUTOLOAD_TEMPLATE_TAGS = getattr(settings, 'MENUWARE_AUTOLOAD_TEMPLATE_TAGS', True)

