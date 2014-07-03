.. _DEPLOYNOTES:

DEPLOYNOTES
===========

Installation
------------

Instructions to install required software and systems, configure the application,
and run various scripts to load initial data.

Software Dependencies
~~~~~~~~~~~~~~~~~~~~~

We recommend the use of `pip <http://pip.openplans.org/>`_ and `virtualenv
<http://virtualenv.openplans.org/>`_ for environment and dependency
management in this and other Python projects. If you don't have them
installed, you can get them with ``sudo easy_install pip`` and then
``sudo pip install virtualenv``.

------

Bootstrapping a development environment
---------------------------------------

* Copy ``readux/localsettings.py.dist`` to ``readux/localsettings.py``
  and configure any local settings: **DATABASES**,  **SECRET_KEY**,
  **SOLR_**, **FEDORA_**,  customize **LOGGING**, etc.
* Create a new virtualenv and activate it.
* Install fabric: ``pip install fabric``
* Use fabric to run a local build, which will install python dependencies in
  your virtualenv, run unit tests, and build sphinx documentation: ``fab build``

Deploy to QA and Production should be done using ``fab deploy``.


After configuring your database, run syncdb:

    python manage.py syncdb

Use eulindexer to index Repository content into the configured Solr instance.

Initial QA/production deploy
----------------------------

* Use fabric deploy method
* Configure localsettings (particularly **DATABASES**, **SOLR**, **FEDORA**,
  **MEDIA_ROOT** and **UPLOAD_TO** settings)

   * Note that Fedora access requires a non-privileged guest account, in order
     to acess an API-M method for information about a datastream, used for
     PDF download view, etc.
* Run ``python manage.py syncdb``
* Configure the site to run under apache (see ``apache/readux.conf`` for a
  sample apache configuration)
* Use Django admin interface to configure the site domain name (used to generate
  absolute urls to full-text content for use with Voyant)
* Configure eulindexer to point to the new site url, restart eulindexer service,
  and reindex the site
* Update/deploy xacml to allow API-A access to LSDI collections
* Run manage script to update Volume PDF ARKs to resolve to the new readux site
  (be sure that the site domain name is configured correctly before running)::

    python manage.py update_arks
