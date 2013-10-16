#!/usr/bin/env bash
# If your site has sitemap.xml that changes often, it is a good idea to let Google know.
# Set PROJ_NAME and DOMAIN_EXTENSION to match that www.settings.default:PROJ_DOMAIN
# Note: It is not a good idea to call Google everytime something changes.
# Instead: Add this script to your cronjob to run as often as you want and no more!
#######################################################################################

PROJ_NAME=djangoware
DOMAIN_EXTENSION=.com
PROJ_DOMAIN=$PROJ_NAME$DOMAIN_EXTENSION
source /srv/www/$PROJ_DOMAIN/pri/venv/bin/activate
cd /srv/www/$PROJ_DOMAIN/pri/venv/webroot
bin/deploy.py ping_google /sitemap.xml

exit

