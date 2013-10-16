#!/usr/bin/env python

import os
from os import path
import sys

# This is a drop-in replacement of Django's (manage.py) to be used when testing.
################################################################################

# Bootstrap Django
for item in ['apps', 'www']:
    sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '../{0}'.format(item))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'settings.test')
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)