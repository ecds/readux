# pylint: disable = not-context-manager
"""Module to deploy Readux to webserver."""
from datetime import datetime
from fabric.contrib.files import exists
from fabric.api import cd, env, run



env.user = 'deploy'

def deploy(branch='release', path='/readux.io/readux', volume=None):
    """Execute group of tasks for deployment.

    :param branch: Git branch to clone, defaults to 'master'
    :type branch: str, optional
    """
    options = {
        'REPO_URL': 'https://github.com/ecds/readux.git',
        'ROOT_PATH': path,
        'VENV_PATH': '{rp}/venv'.format(rp=path),
        'RELEASE_PATH': '{rp}/releases'.format(rp=path),
        'VERSION': datetime.now().strftime("%Y%m%d%H%M%S")
    }

    version_folder = '{rp}/{vf}'.format(rp=options['RELEASE_PATH'], vf=options['VERSION'])
    run('mkdir -p {p}'.format(p=version_folder))

    with cd(version_folder):
        # _create_new_dir()
        _get_latest_source(branch, options)
        _update_virtualenv(options)
        _link_settings(options)
        _create_staticfiles_symlink(options)
        if volume is not None:
            _mount_media(volume)
        _update_static_files(options)
        _update_database(options)
        _update_symlink(options)
        _restart_webserver()
        _restart_celery(options)
        _rebuild_search_index(options)
        _clean_old_builds(options)

def _get_latest_source(branch, options):
    """Clones latest commit from given git branch.

    :param branch: Git branch to clone.
    :type branch: str
    """
    run('git clone {r} .'.format(r=options['REPO_URL']))
    run('git checkout {b}'.format(b=branch))

def _update_virtualenv(options):
    """Set up python virtual environment.
    """
    if not exists('{v}/bin/pip'.format(v=options['VENV_PATH'])):
        run('python3 -m venv {v}'.format(v=options['VENV_PATH']))
    run('{v}/bin/pip install -r requirements/local.txt'.format(v=options['VENV_PATH']))
    run('ln -s {rp}/.ruby-version .ruby-version'.format(rp=options['ROOT_PATH']))
    run('~/.rbenv/shims/gem install bundler -v "$(grep -A 1 "BUNDLED WITH" Gemfile.lock | tail -n 1)"') # pylint: disable = line-too-long
    run('~/.rbenv/shims/bundle install')
    run('/usr/bin/npm install')
    run('/usr/bin/npx webpack')

def _link_settings(options):
    """Make sym link to settings file stored on the server.
    """
    with cd('config/settings'):
        run('ln -s {rp}/local.py local.py'.format(rp=options['ROOT_PATH']))

def _mount_media(volume):
    with cd('apps'):
        run(f'mkdir media && sudo mount /dev/{volume} media')

def _create_staticfiles_symlink(options):
    run('ln -s {rp}/staticfiles staticfiles'.format(rp=options['ROOT_PATH']))

def _update_static_files(options):
    run('rm package-lock.json && npm install && npx webpack')
    run('{v}/python manage.py compilescss && {v}/bin/python manage.py collectstatic --noinput'.format(v=options['VENV_PATH']))

def _update_database(options):
    run('{v}/bin/python manage.py migrate --noinput'.format(v=options['VENV_PATH']))

def _update_symlink(options):
    with cd(options['ROOT_PATH']):
        if exists('{rp}/current'.format(rp=options['ROOT_PATH'])):
            run('rm {rp}/current'.format(rp=options['ROOT_PATH']))
        run('ln -s {rp}/releases/{v} current'.format(rp=options['ROOT_PATH'], v=options['VERSION']))

def _restart_webserver():
    run('sudo /bin/systemctl reload apache2')

def _restart_celery(options):
    run('sudo /bin/systemctl restart celeryd')

def _rebuild_search_index(options):
    run('{v}/bin/python manage.py search_index --rebuild -f'.format(v=options['VENV_PATH']))

def _clean_old_builds(options):
    with cd(options['RELEASE_PATH']):
        run('rm -rf $(ls -1t . | tail -n +11)')
