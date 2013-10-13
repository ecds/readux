from django.contrib.sites.models import Site

import defaults

# Current Site Object (site: name, site: domain)
SITE_OBJECT_CURRENT = getattr(settings, 'SITE_OBJECT_CURRENT', Site.objects.get_current())

def contextify(request):
    """ Bring few goodies into the context. """

    ctx = {
        'SITE_ORG': defaults.SITE_ORG,
        'SITE_NAME': defaults.SITE_NAME,
        'SITE_DOMAIN': defaults.SITE_DOMAIN,
        'SITE_PROTOCOL': defaults.SITE_PROTOCOL or (request.is_secure() and 'https' or 'http'),
        'SITE_TITLE': defaults.SITE_TITLE,
        'SITE_KEYWORDS': defaults.SITE_KEYWORDS,
        'SITE_DESCRIPTION': defaults.SITE_DESCRIPTION,
        'SITE_COMMON_DOWNLOADABLE_STATIC_URL': defaults.SITE_COMMON_DOWNLOADABLE_STATIC_URL,
        'SITE_COMMON_STREAMING_STATIC_URL': defaults.SITE_COMMON_STREAMING_STATIC_URL,
        'SITE_GOOGLE_ANALYTICS': defaults.SITE_GOOGLE_ANALYTICS,
        'SITE_OBJECT_CURRENT': SITE_OBJECT_CURRENT,
    }

    return ctx

