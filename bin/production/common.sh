##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

# Runs bash commands as sudo
############################################

# Collects project's static files
############################################
function statics_collect {
    source /srv/www/neekware.io/pri/venv/bin/activate
    cd /srv/www/neekware.io/pri/venv/webroot
    git pull
    git checkout production
    git pull
    pip install -r env/requirements/production.txt
    bin/production/manage.py collectstatic --noinput
    cd -
}

# Updates project's secret files
############################################
function secrets_update {
    cd /srv/www/seekrets/neekware.io
    git pull
    git checkout production
    git pull
    cd -
}

# Updates the project
############################################
function project_update {
    source /srv/www/neekware.io/pri/venv/bin/activate
    cd /srv/www/neekware.io/pri/venv/webroot
    git pull
    git checkout production
    git pull
    ln -sf /srv/www/seekrets/neekware.io/back/seekrets/seekrets.pro.json seekrets.json
    pip install -r env/requirements/production.txt
    bin/production/manage.py compilemessages
    bin/production/manage.py loadxlates
    cd -
}

# Migrate project's code/db
############################################
function project_migrate {
    source /srv/www/neekware.io/pri/venv/bin/activate
    cd /srv/www/neekware.io/pri/venv/webroot
    git pull
    git checkout production
    git pull
    pip install -r env/requirements/production.txt
    bin/production/manage.py migrate
    cd -
}

# Restart web server
#############################################
function server_restart {
    supervisorctl stop neekware.io
    supervisorctl start neekware.io
}
