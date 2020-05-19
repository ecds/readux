"""Exposes the custom style to the base template."""
from .models import Style

def add_custom_style(request):
    """Return user defined CSS.

    :param request: Current Request
    :type request: django.HttpRequest
    :return: CSS from active style.
    :rtype: str
    """
    try:
        active_style = Style.objects.get(active=True)
        if active_style:
            return {'css': active_style.css}
    except Style.DoesNotExist:
        pass
    return {'css': ''}
