import os
from django.conf import settings
from django.contrib.sites.models import Site

import defaults

# Setup the sites available for this project
def setup_sites():
    """
    Setup sites (name, domain) available for this project (SITE_ID will decide the active site)
    """
    site_info = getattr(defaults, 'SITE_OBJECTS_INFO_DICT')
    if site_info:
        for pk in sorted(site_info.iterkeys()):
            site, created = Site.objects.get_or_create(pk=pk)
            if site:
                site.name = site_info[pk]['name']
                site.domain = site_info[pk]['domain']
                site.save()



