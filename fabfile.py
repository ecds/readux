from datetime import datetime
from fabric.contrib.files import append, exists
from fabric.api import cd, env, local, run

REPO_URL = 'https://github.com/ecds/readux.git'
ROOT_PATH = '/data/readux'
VENV_PATH = '{rp}/venv'.format(rp=ROOT_PATH)
RELEASE_PATH = '{rp}/releases'.format(rp=ROOT_PATH)
VERSION = datetime.now().strftime("%Y%m%d%H%M%S")

env.user = 'deploy'

def deploy(branch='master'):
    version_folder = '{rp}/{vf}'.format(rp=RELEASE_PATH, vf=VERSION)
    run('mkdir -p {p}'.format(p=version_folder))  
    with cd(version_folder):
        # _create_new_dir() 
        _get_latest_source(branch)
        _update_virtualenv()
        _create_or_update_settings()
        _create_static_media_symlinks()
        _update_static_files()
        _update_database()
        _update_symlink()
        _restart_webserver()
        _restart_export_task()
        _clean_old_builds()

def _get_latest_source(branch):
    run('git clone {r} .'.format(r=REPO_URL))
    run('git checkout {b}'.format(b=branch))

def _update_virtualenv():
    if not exists('{v}/bin/pip'.format(v=VENV_PATH)):  
        run('python3 -m venv {v}'.format(v=VENV_PATH))
    run('{v}/bin/pip install -r requirements/local.txt'.format(v=VENV_PATH))
    run('~/.rbenv/shims/gem install bundler -v "$(grep -A 1 "BUNDLED WITH" Gemfile.lock | tail -n 1)"')
    run('~/.rbenv/shims/bundle install')

def _create_or_update_settings():
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
    run('kill $(<{rp}/export.pid)').format(rp=ROOT_PATH)
    run('nohup {v}/bin/python manage.py process_tasks > /dev/null 2>&1 & echo $! > {rp}/export.pid').format(v=VENV_PATH, rp=ROOT_PATH)

def _clean_old_builds():
    with cd(RELEASE_PATH):
        run('rm -rf $(ls -1t . | tail -n +6)')