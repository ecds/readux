import os
import sys

from .defaults import *

# Flavor of the server running this code
DJANGO_SERVER_TYPE = os.environ.get('DJANGO_SERVER_TYPE', 'UNKNOWN')

# Flavor of the configuration file
CONFIG_FLAVOR = str(CONFIG_DATA['CONFIG_FLAVOR']).upper()
