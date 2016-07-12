import os

from .base.deployable import *

DEBUG = True

if DJANGO_SERVER_TYPE != 'DEVELOPMENT':
    warnings.warn('Invalid Django server type. {}'.format(DJANGO_SERVER_TYPE))
    sys.exit(0)

if CONFIG_FLAVOR != 'DEVELOPMENT':
    warnings.warn('Invalid Django settings file. {}'.format(CONFIG_FLAVOR))
    sys.exit(0)
