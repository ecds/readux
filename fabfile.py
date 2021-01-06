# pylint: disable = not-context-manager
"""Module to deploy Readux to webserver."""
from datetime import datetime
from fabric.contrib.files import exists
from fabric.api import cd, env, run

REPO_URL = 'https://github.com/ecds/readux.git'
ROOT_PATH = '/data/readux'
VENV_PATH = '{rp}/venv'.format(rp=ROOT_PATH)
RELEASE_PATH = '{rp}/releases'.format(rp=ROOT_PATH)
VERSION = datetime.now().strftime("%Y%m%d%H%M%S")

env.user = 'deploy'

def deploy(branch='master'):
    """Execute group of tasks for deployment.

    :param branch: Git branch to clone, defaults to 'master'
    :type branch: str, optional
    """

    version_folder = '{rp}/{vf}'.format(rp=RELEASE_PATH, vf=VERSION)
    run('mkdir -p {p}'.format(p=version_folder))

    with cd(version_folder):
        # _create_new_dir()
        _get_latest_source(branch)
        _update_virtualenv()
        _link_settings()
        _create_static_media_symlinks()
        _update_static_files()
        _update_database()
        _update_symlink()
        _restart_webserver()
        _restart_export_task()
        _clean_old_builds()

def _get_latest_source(branch):
    """Clones latest commit from given git branch.

    :param branch: Git branch to clone.
    :type branch: str
    """
    run('git clone {r} .'.format(r=REPO_URL))
    run('git checkout {b}'.format(b=branch))

def _update_virtualenv():
    """Set up python virtual environment.
    """
    if not exists('{v}/bin/pip'.format(v=VENV_PATH)):
        run('python3 -m venv {v}'.format(v=VENV_PATH))
    run('{v}/bin/pip install -r requirements/local.txt'.format(v=VENV_PATH))
    run('ln -s {rp}.ruby-version .ruby-version'.format(rp=ROOT_PATH))
    run('~/.rbenv/shims/gem install bundler -v "$(grep -A 1 "BUNDLED WITH" Gemfile.lock | tail -n 1)"') # pylint: disable = line-too-long
    run('~/.rbenv/shims/bundle install')

def _link_settings():
    """Make sym link to settings file stored on the server.
    """
    with cd('config/settings'):
        run('ln -s {rp}/local.py local.py'.format(rp=ROOT_PATH))

def _create_static_media_symlinks():
    run('ln -s {rp}/staticfiles staticfiles'.format(rp=ROOT_PATH))
    with cd('apps'):
        run('ln -s {rp}/media'.format(rp=ROOT_PATH))

def _update_static_files():
    run('{v}/bin/python manage.py collectstatic --noinput'.format(v=VENV_PATH))

def _update_database():
    run('{v}/bin/python manage.py migrate --noinput'.format(v=VENV_PATH))

def _update_symlink():
    with cd(ROOT_PATH):
        if exists('{rp}/current'.format(rp=ROOT_PATH)):
            run('rm {rp}/current'.format(rp=ROOT_PATH))
        run('ln -s {rp}/releases/{v} current'.format(rp=ROOT_PATH, v=VERSION))

def _restart_webserver():
    run('sudo service apache2 restart')

def _restart_export_task():
    run('bash {rp}/restart_export_task.sh'.format(rp=ROOT_PATH))

def _clean_old_builds():
    with cd(RELEASE_PATH):
        run('rm -rf $(ls -1t . | tail -n +6)')
