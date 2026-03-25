"""Exposes the custom style to the base template."""
from .models import Style
from django.conf import settings

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

def background_image_url(request):
    """
    Add BACKGROUND_IMAGE_URL and a fallback gradient to the template context.
    """
    return {
        'background_image_url': getattr(settings, 'BACKGROUND_IMAGE_URL', ''),
        'background_fallback': 'linear-gradient(135deg, #1D3557, #457B9D)',  # Fallback gradient
    }