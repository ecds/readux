"""
Expose specific app settings to templates.
"""
from django.conf import settings

def has_ga_tracking_id(request):
    """Return `True` if `settings.GOOGLE_ANALYTICS_ID` has been set."""
    if hasattr(settings, 'GOOGLE_ANALYTICS_ID'):
        has_ga_id = settings.GOOGLE_ANALYTICS_ID is not None
    else:
        has_ga_id = False

    return {
        'has_ga_tracking_id': has_ga_id
        }

def ga_tracking_id(request):
    """Expose ID for Google Analytics to the templates."""
    if hasattr(settings, 'GOOGLE_ANALYTICS_ID'):
        return {
            'ga_tracking_id': settings.GOOGLE_ANALYTICS_ID
        }
    return {}
