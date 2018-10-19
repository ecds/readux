Django Backend Starter
======================

**A simple Django starter project**

Overview
======================

**Djangoware** attempts to layout a Django project based on the best practices

This is a starter project and it's meant to speed up your development to production process.  Many measures have been taken to ensure your production instance(s) remain secure.  You still need to make it your own!

Please note that Djangoware is not an installable application.  Djangoware can be considered as a blueprint of your next Django project.  Simply fork the project, rename it to what you want and modify seekrets.json to reflect your needs.

Notice
======================
Djangoware uses Django 2+, hence it ONLY works with Python 3.

How to use (DEVELOPMENT)
======================
```
$ export DEPLOYMENT_FLAVOR='DEVELOPMENT'
$ python3 -m venv myenv
$ cd myenv
$ source bin/activate
$ pip install --upgrade pip
$ git clone https://github.com/un33k/djangoware.git
$ cd djangoware
$ git checkout development
$ cp seekrets_example/dev.seekrets.example.json seekrets.json
$ pip install -r env/requirements/development.txt
$ bin/development/manage.py migrate
$ bin/development/manage.py runserver 0.0.0.0:8181
```
**Note:**
1. Modify seekrets.json as per your development requirements
2. Ensure that seekrets.json is stored in a separate private repo
3. Default development database is sqlite

How to use (PRODUCTION)
======================
```
$ export DEPLOYMENT_FLAVOR='PRODUCTION'
$ python3 -m venv myenv
$ cd myenv
$ source bin/activate
$ pip install --upgrade pip
$ git clone https://github.com/un33k/djangoware.git
$ cd djangoware
$ git checkout production
$ cp seekrets_example/pro.seekrets.example.json seekrets.json
$ pip install -r env/requirements/production.txt
$ bin/production/manage.py migrate
$ bin/production/manage.py collectstatic
```
**Note:**
1. Modify seekrets.json as per your production requirements
2. Ensure that seekrets.json is stored in a separate private repo
3. The `collectstatic` stores the static artifacts in `assets/collect` by default
4. If AWS credentials are set in seekrets.json, `collectstatic` stores the static artifacts to your `S3` buckets.
5. Use `www/wsgi/production.py` with your production webserver

How to TEST
======================
```
$ export DEPLOYMENT_FLAVOR='DEVELOPMENT'
$ python3 -m venv myenv
$ cd myenv
$ source bin/activate
$ pip install --upgrade pip
$ git clone https://github.com/un33k/djangoware.git
$ cd djangoware
$ git checkout development
$ cp seekrets_example/dev.seekrets.example.json seekrets.json
$ pip install -r env/requirements/development.txt
$ bin/development/manage.py migrate
$ bin/test/api_test.sh -a
```
