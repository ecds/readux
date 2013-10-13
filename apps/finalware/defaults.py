from django.conf import settings

# Automatically create the site objects for this website
SITE_OBJECTS_INFO_DICT = getattr(settings, 'SITE_OBJECTS_INFO_DICT', None)

# Location of common downloadable static assests (example: Amazon S3 bucket configured for downloading)
SITE_COMMON_DOWNLOADABLE_STATIC_URL = getattr(settings, 'SITE_COMMON_DOWNLOADABLE_STATIC_URL', '')

# Location of common streaming media assests (example: Amazon S3 bucket configured for streaming)
SITE_COMMON_STREAMING_STATIC_URL = getattr(settings, 'SITE_COMMON_STREAMING_STATIC_URL', '')

# Site Specific Info
SITE_ORG = getattr(settings, 'SITE_ORG', 'MyOrg')
SITE_NAME = getattr(settings, 'PROJ_NAME', 'MySite')
SITE_DOMAIN = getattr(settings, 'PROJ_DOMAIN', 'mysite.com')
SITE_PROTOCOL = getattr(settings, 'SITE_PROTOCOL', '')
SITE_TITLE = getattr(settings, 'SITE_TITLE', SITE_DOMAIN.upper())
SITE_KEYWORDS = getattr(settings, 'SITE_KEYWORDS', 'MyOrg MySite Related Keywords')
SITE_DESCRIPTION = getattr(settings, 'SITE_DESCRIPTION', 'This is a Django-Powered Site.')

# Google Analytics for this site
SITE_GOOGLE_ANALYTICS = getattr(settings, 'SITE_GOOGLE_ANALYTICS', '')

# Autoload template tags in this list
AUTO_LOAD_TEMPLATE_TAGS_LIST = getattr(settings, 'AUTO_LOAD_TEMPLATE_TAGS_LIST', [])


