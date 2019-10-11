from datetime import datetime
from fabric.contrib.files import append, exists
from fabric.api import cd, env, local, run

REPO_URL = 'https://github.com/ecds/readux.git'
ROOT_PATH = '/data/readux'
VENV_PATH = '{rp}/venv'.format(rp=ROOT_PATH)
VERSION = datetime.now().strftime("%Y%m%d%H%M%S")
env.user = 'deploy'
env.hosts = ['52.71.44.91']

def deploy():

    version_folder = '{rp}/{vf}'.format(rp=ROOT_PATH, vf=VERSION)
    run('mkdir -p {p}'.format(p=version_folder))  
    with cd(version_folder):
        # _create_new_dir() 
        _get_latest_source()
        _update_virtualenv()
        _create_or_update_settings()
        _update_static_files()
        _update_database()
        _update_symlink()
        _restart_webserver()

def _get_latest_source():
    run('git clone {r} .'.format(r=REPO_URL))

def _update_virtualenv():
    if not exists('{v}/bin/pip'.format(v=VENV_PATH)):  
        run('python3 -m venv {v}'.format(v=VENV_PATH))
    run('{v}/bin/pip install -r requirements/local.txt'.format(v=VENV_PATH))
    run('sudo gem install bundler')
    run('bundle install')

def _create_or_update_settings():
    with cd('config/settings'):
        run('ln -s {rp}/local.py local.py'.format(rp=ROOT_PATH))

def _update_static_files():
    run('{v}/bin/python manage.py collectstatic --noinput'.format(v=VENV_PATH))

def _update_database():
    run('{v}/bin/python manage.py migrate --noinput'.format(v=VENV_PATH))

def _update_symlink():
    with cd('../'):
        if exists('{rp}/current'.format(rp=ROOT_PATH)):
            run('rm {rp}/current'.format(rp=ROOT_PATH))
        run('ln -s {rp}/{v} current'.format(rp=ROOT_PATH, v=VERSION))

def _restart_webserver():
    run('sudo service apache2 restart')