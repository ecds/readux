# Readux

...

## Motivation

...

### Deployment

...

## Installation (development)

### Requirements

1. Python 3
2. PostgreSQL

### Set up development environment

1. Clone this repository
2. Navigate to the readux directory
3. Create virtual environment

~~~bash
python3 -m venv venv
source venv/bin/activate
~~~

4. Install dependencies

~~~bash
pip install -r requirements/local
~~~

5. Copy and set up your local settings

~~~bash
cp config/settings/local.dst config/settings/local.py
~~~

6. Add your database settings to the local.py file or set an environment variable. For example:

~~~bash
export DATABASE_URL=postgres://<database user>:<database password>@127.0.0.1:5432/<database name>
~~~

7. Run the migrations and load the example data

~~~bash
python manage.py migrate
python manage.py loaddata apps/fixtures/dump.json
~~~

## Contribute

We use the [Git-Flow](https://danielkummer.github.io/git-flow-cheatsheet/) branching model. Pull requests should be made against the develop branch.

## Tech/framework used

![Build with Cookiecutter Django][https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg](https://github.com/pydanny/cookiecutter-django/)

[Mirador](http://projectmirador.org/) for displaying and annotating [IIIF](http://iiif.io) images.

??? for exporting.

## License

This software is distributed under the Apache 2.0 License.