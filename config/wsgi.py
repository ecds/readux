import os, sys
INTERP = "/data/readux/env/bin/python3.5"
PYTHON_BIN = INTERP
if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)
sys.path.insert(0,'/data/readux/env/bin')

from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()