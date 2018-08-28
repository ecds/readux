INSTALLED_APPS = (
    'readux.annotations.apps.config',
)

THIRD_PARTY_APPS = (
    'rest_framework',
)

REST_FRAMEWORK = {
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': 'db.cnf',
        },
    }
}

try:
   from local_settings import *
except ImportError:
    raise Exception("A local_settings.py file is required to run this project")