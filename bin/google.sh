#!/usr/bin/env bash
# If your site has sitemap.xml that changes often, it is a good idea to let Google know.
# Set SITE_PROJ_NAME and DOMAIN_EXTENSION to match that www.settings.default:SITE_DOMAIN_NAME
# Note: It is not a good idea to call Google everytime something changes.
# Instead: Add this script to your cronjob to run as often as you want and no more!
#######################################################################################

SITE_PROJ_NAME=djangoware
DOMAIN_EXTENSION=.org
SITE_DOMAIN_NAME=$SITE_PROJ_NAME$DOMAIN_EXTENSION
source /srv/www/$SITE_DOMAIN_NAME/pri/venv/bin/activate
cd /srv/www/$SITE_DOMAIN_NAME/pri/venv/webroot
bin/production.py ping_google /sitemap.xml

exit

