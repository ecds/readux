# Readux

Readux is a platform developed by the Emory Center for Digital Scholarship which allows users to read, take notes on, and publish with digitized texts from libraries’ archival collections. With Readux, users are able to:
-	browse digitized page images, 
-	search and select the texts of these digitized books, 
-	annotate text or illustrations in these works, and then 
-	publish digital copies of the texts with their annotations. 
Administrators can organize digitized books into collections, facilitating user access to digitized books available through the platform. Since its release, Readux has proved to be an innovative research and pedagogy tool for scholars and faculty at Emory University and beyond, with an array of use-cases ranging from teaching to publishing. 


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

### Running local development server

Run the development under https. Note: this is generate a self-signed certificate. There are ways tell your browser to trust these certs, but that is beyond the scope of this README.

~~~bash
python manage.py runserver_plus --cert-file cert.crt  0.0.0.0:3000
~~~

### Running the tests

Readux uses Django's default test framework.

~~~bash
python manage.py test
~~~

## Contribute

We use the [Git-Flow](https://danielkummer.github.io/git-flow-cheatsheet/) branching model. Pull requests should be made against the develop branch.

### Code of conduct

[Code of Conduct](CODE_OF_CONDUCT.md)

## Tech/framework used

[![Build with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg)](https://github.com/pydanny/cookiecutter-django/)

[Mirador](http://projectmirador.org/) for displaying and annotating [IIIF](http://iiif.io) images.

??? for exporting.

## License

This software is distributed under the Apache 2.0 License.
