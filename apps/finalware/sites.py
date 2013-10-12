import os
from django.conf import settings
from django.contrib.sites.models import Site

import defaults

# Setup the sites available for this project
def setup_sites():
    """
    Setup sites (name, domain) available for this project (SITE_ID will decide the active site)
    """
    site_info = getattr(defaults, 'SITE_OBJECTS_INFO')
    if site_info:
        site_ids = site_info.keys()
        for pk in site_ids.sort():
            site, created = Site.objects.get_or_create(pk=pk)
            if site:
                site.name = site_info[pk]['name']
                site.domain = site_info[pk]['domain']
                site.save()



