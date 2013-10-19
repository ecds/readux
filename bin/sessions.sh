#!/usr/bin/env bash
# If you are storing the user sessions in DB, it is a good idea to purge them often.
# Set PROJ_NAME and DOMAIN_EXTENSION to match that www.settings.default:PROJ_DOMAIN
###################################################################################

PROJ_NAME=djangoware
DOMAIN_EXTENSION=.org
PROJ_DOMAIN=$PROJ_NAME$DOMAIN_EXTENSION
source /srv/www/$PROJ_DOMAIN/pri/venv/bin/activate
cd /srv/www/$PROJ_DOMAIN/pri/venv/webroot
bin/deploy.py clearsessions

exit

