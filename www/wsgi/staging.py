##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###


import os
import sys
import site
import platform
from os import path

sys.stdout = sys.stderr  # wsgi doesn't support stdout
os.environ['DEPLOYMENT_FLAVOR'] = 'STAGING'

VIRTUAL_ENV_PATH = path.abspath(path.join(path.dirname(__file__), "../../../"))
PYTHON_VERSION = "lib%s/site-packages" % platform.python_version()[:3]
SITE_PACKAGES = path.join(VIRTUAL_ENV_PATH, PYTHON_VERSION)

# Remember original sys.path.
prev_sys_path = list(sys.path)

# Add each new site-packages directory.
site.addsitedir(SITE_PACKAGES)

# Reorder sys.path so new directories are available first.
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

activate_this = path.join(VIRTUAL_ENV_PATH, 'bin', 'activate_this.py')
with open(activate_this) as f:
    code = compile(f.read(), activate_this, 'exec')
    exec(code, dict(__file__=activate_this))

# Bootstrap Django
for item in ['api', 'apps', 'www']:
    sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '../../{0}'.format(item))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'settings.staging')


def get_app():
    from django.core.wsgi import get_wsgi_application
    return get_wsgi_application()


application = get_app()
