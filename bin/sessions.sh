#!/usr/bin/env bash
# If you are storing the user sessions in DB, it is a good idea to purge them often.
# Set SITE_PROJ_NAME and DOMAIN_EXTENSION to match that www.settings.default:SITE_DOMAIN_NAME
###################################################################################

SITE_PROJ_NAME=djangoware
DOMAIN_EXTENSION=.org
SITE_DOMAIN_NAME=$SITE_PROJ_NAME$DOMAIN_EXTENSION
source /srv/www/$SITE_DOMAIN_NAME/pri/venv/bin/activate
cd /srv/www/$SITE_DOMAIN_NAME/pri/venv/webroot
bin/production.py clearsessions

exit

