from os import environ
from git import Repo
from django.conf import settings
from . import __version__

def current_version(request=None):
    repo = Repo(settings.ROOT_DIR.path())

    version_info = {
        'DJANGO_ENV': environ['DJANGO_ENV'],
        'APP_VERSION': __version__
    }

    if environ['DJANGO_ENV'] == 'production':
        return version_info
    else:
        return {
            **version_info,
            'BRANCH': repo.active_branch.name,
            'COMMIT': repo.active_branch.commit.hexsha,
            'COMMIT_DATE': repo.active_branch.commit.committed_datetime.strftime("%m/%d/%Y, %H:%M:%S")
        }
