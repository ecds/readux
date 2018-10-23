# README

## Readux

Readux is a repository-based [Django](https://www.djangoproject.com/) 
web application for access to digitized books.

Documentation available at
`readux.readthedocs.org <http://readux.readthedocs.org/en/develop/>`_.

## License

This software is distributed under the Apache 2.0 License.

## Dependencies

### Services

- PostgreSQL database for administration, user accounts, collection banner images, and annotation storage.

### Software Dependencies

## Components

```readux.collection```

Models and views for access to collections, which are used to group digitized book content

``readux.volumes``

Models and views for access to digizited book content

``readux.annotations``

Django db models and views to provide a RESTful API to an annotator-store endpoint;
implements the [Web Annotation Data Model](https://www.w3.org/TR/annotation-model/) for use in [Mirador](http://projectmirador.org/).

## Development

This project uses the [git-flow](http://danielkummer.github.io/git-flow-cheatsheet/index.html) model.

### Clone the repository

~~~shell
git clone https://github.com/ecds/readux.git
cd readux
# If you installed git-flow. Accept all the defaults.
git flow init
# Make sure you are in the develop branch
git checkout develop
~~~

### Setup Virtual Environment

_This might vary based on your local env._

~~~shell
python3.5 -m venv env
source env/bin/activate
pip install -r requirements/minimum.txt
~~~

### Create a postgres database

_However you do this in your env._

### Set up your `localsettings.py`

Copy the example and add your local database info:

~~~shell
cp config/localsettings.py.dist config/localsettings.py
vim config/localsettigns.py
~~~

### Setup the Database

~~~shell
./manage.py migrate
~~~

### Start the Development Server

~~~shell
python manage.py runserver
~~~

By visiting [http://localhost:3000](http://localhost:3000) you should see an ordered list of collections.

### Starting a new feature

#### With Git Flow

~~~shell
git flow feature start <name of feature>
~~~

#### Without Git Flow

~~~shell
git checkout feature/<name of feature>
~~~

### Submitting Pull Request

Make PRs to the `develop` branch

#### With Git Flow

~~~shell
git flow feature finish <name of feature>
~~~

#### Without Git Flow

~~~shell
git checkout develop
git merge feature/<name of feature>
~~~
