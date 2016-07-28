.. _DEPLOYNOTES:

Installation and Deploy
=======================

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

For annotated edition export functionality, the digital edition jekyll theme
automatically handled as a python dependency but the
`teifacsimile-to-jekyll <https://github.com/emory-libraries-ecds/teifacsimile-to-jekyll>`_
Ruby gem must currently be installed manually.

Initial QA/production deploy
----------------------------

* Use fabric deploy method
* Configure localsettings (particularly **DATABASES**, **SOLR**, **FEDORA**,
  **MEDIA_ROOT** and **UPLOAD_TO** settings)

   * Note that Fedora access requires a non-privileged guest account, in order
     to acess an API-M method for information about a datastream, used for
     PDF download view, etc.

* Run ``python manage.py syncdb``
* Run ``python manage.py migrate``
* Configure the site to run under apache (see ``deploy/apache/readux.conf`` for a
  sample apache configuration)
* Use Django admin interface to configure the site domain name (used to generate
  absolute urls to full-text content for use with Voyant)
* Use Django console to update LSDI collection objects with an owner value
  that can be used for xacml policies and filtering::

     python manage.py shell
     >>> from readux.fedora import ManagementRepository
     >>> from readux.collection.models import Collection
     >>> repo = ManagementRepository()
     >>> colls = repo.get_objects_with_cmodel(Collection.COLLECTION_CONTENT_MODEL, type=Collection)
     >>> for c in colls:
     ...    if 'LSDI' in c.label:
     ...        c.owner = 'LSDI-project'
     ...        c.save('set owner to "LSDI-project" for xacml policy')
     ...

* Configure eulindexer to point to the new site url, restart eulindexer service,
  and reindex the site
* Update/deploy xacml to allow API-A access to LSDI collections

* Run a manage script to populate initial collection descriptions::

    python manage.py collection_descriptions


Upgrade Notes
-------------

**Patch affects all releases until further notice**

Readux is currently affected by a bug in Django's debug logic; a patch is available
but not yet included in any official Django releases.  To apply this patch to the
locally installed copy of Django, use the patch file included in the deploy
directory.  From the top level of your virtualenv directory, run::

    patch -p0 < django-views-debug.patch

----

Release 1.6
~~~~~~~~~~~

* Run migrations for database updates::

      python manage.py migrate

* Configure Amazon S3 settings for temporary storage of background export
  for downloaded zip files.  See the required fields in
  ``localsettings.py.dist``.

* This release makes use of Channels.  See the
  `channels deploy documentation <https://channels.readthedocs.io/en/latest/deploying.html>`_
  and configure **CHANNEL_LAYERS** in ``localsettings.py``.

Release 1.5
~~~~~~~~~~~

* Zotero should be configured as a social authentication backend
  to support citation lookups.  Add OAuth keys based on the example
  configuration in ``localsettings.py.dist``

Release 1.4
~~~~~~~~~~~

* Basic export functionality requires the teifacsimile-to-jekyll gem
  version 0.5 be installed (available from
  `0.5 release <https://github.com/emory-libraries-ecds/teifacsimile-to-jekyll/releases/tag/0.5.0>`_
  on GitHub).

  The application expects the jekyll and jekyllimport_teifacsimile
  commands to be available in the configured environment path.  One way
  to do this is by creating a file to be sourced when users login and
  by /etc/sysconfig/httpd.  Example environment file::

      source /opt/rh/rh-ruby22/enable
      source /opt/rh/python27/enable
      export PATH=$PATH:/opt/rh/rh-ruby22/root/usr/local/bin

* The GitHub export uses new **GIT_AUTHOR_EMAIL** and **GIT_AUTHOR_NAME**
  configurations; defaults are included in ``settings.py``, but can
  be overridden in ``localsettings.py``.

Release 1.3
~~~~~~~~~~~

* Some page images in Fedora have a generic mimetype, which Loris can't
  handle for recognizing and generating images.  Before switching to the
  new version, these should be cleaned up in the python console::

    from readux.fedora import ManagementRepository
    from readux.books.models import PageV1_0
    repo = ManagementRepository()
    query = '''select ?pid
    where {
      ?pid <fedora-model:hasModel> <info:fedora/emory-control:ScannedPage-1.0> .
      ?pid <fedora-view:disseminates> ?ds .
      ?ds <fedora-view:mimeType> 'application/octet-stream'
    }'''
    results = repo.risearch.find_statements(query, language='sparql', type='tuples')
    for n in results:
      page = repo.get_object(n['pid'], type=PageV1_0)
      if page.image.mimetype == 'application/octet-stream':
         page.image.mimetype = 'image/jp2'
         page.save('Updating image mimetype')
         print 'Updated %s' % n['pid']

* The new IIIF-based image handling requires new configurations be added
  to ``localsettings.py``: **IIIF_API_ENDPOINT** and **IIIF_ID_PREFIX**
  (prefix is optional, depending on configuration).  See
  ``localsettings.py.dist`` for an example.

* Run migrations for database updates::

      python manage.py migrate

* If using MySQL, make sure the database has time zone data loaded:
  http://dev.mysql.com/doc/refman/5.7/en/mysql-tzinfo-to-sql.html

* The URL format for pages has changed; update page ARK records by
  running a script::

      python manage.py update_page_arks

* Generate TEI for all volumes with pages loaded:

      python manage.py add_pagetei --all

* The dependency on :mod:`eullocal` has been removed, so if you are using
  an existing virtualenv, eullocal can be uninstalled after this upgrade.


Release 1.2.1
~~~~~~~~~~~~~

* The dependency on :mod:`eullocal` has been removed, so eullocal can
  be uninstalled after upgrading if re-using a pre-existing virtualenv.
* Update ``localsettings.py`` to set **DOWNTIME_ALLOWED_IPS** to any IP
  addresses that should be allowed to access the site during configured
  downtime periods.

Release 1.2
~~~~~~~~~~~

* This release includes an update to Django 1.7 and includes new database
  migrations.  To update the database, run::

      python manage.py migrate

* LDAP login is now handled by `django-auth-ldap <https://pythonhosted.org/django-auth-ldap/>`_.  LDAP
  configuration settings will need to be updated in ``localsettings.py``;
  see example configuration in ``localsettings.py.dist``.

* Configure new setting **TEI_DISTRIBUTOR** in ``localsettings.py``.
  See example configuration in ``localsettings.py.dist``.

* Readux now supports social authentication via Twitter, Google, GitHub,
  Facebook, etc.  OAuth keys for each of the configured backends should
  be requested and configured in ``localsettings.py``.  The list of enabled
  authentication backends can also be overridden in localsettings, if
  needed.

Release 1.1
~~~~~~~~~~~

* Update Fedora XACML policies to include new variant content models
  (ScannedVolume-1.1 and ScannedPage-1.1) and reload policies so that newly
  ingested content will be accessible.

* Restart eulindexer so it will pick up the new content models to be indexed.

* Configure new setting **LARGE_PDF_THRESHOLD** in ``localsettings.py``.
  See sample config and default value in ``localsettings.py.dist``.

Release 1.0.2
~~~~~~~~~~~~~

* Run **syncrepo** manage script to ensure all Fedora content models are
  loaded in the configured repository::

    python manage.py syncrepo

Release 1.0
~~~~~~~~~~~

* Run the manage script to import covers for all books::

    python manage.py import_covers

  or by collection::

    python manage.py import_covers -c emory-control:LSDI-Yellowbacks

.. Note::

    Ingesting page images requires access to the Digitization Workflow
    web application and file-level access to the content managed by the
    Digitization Workflow (e.g., /mnt/lsdi).

* Run the manage script to import pages for *selected* books by pid::

    python manage.py import_covers pid1 pid2 pid3 ...

  or by collection::

    python manage.py import_pages -c emory-control:LSDI-Yellowbacks
