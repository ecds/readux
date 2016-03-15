.. _README:

Readux
------

Overview
^^^^^^^^

Readux is a repository-based `Django <https://www.djangoproject.com/>`_
web application for access to digitized books.  Readux runs on
`Fedora Commons 3.8 <https://wiki.duraspace.org/display/FEDORA38/Fedora+3.8+Documentation>`_
and Django 1.8.  Readux provides search and browse access to all digitized
books, citations that can be harvested with `Zotero <https://www.zotero.org/>`_,
the ability to send text to `Voyant <http://voyant-tools.org/>`_ for analysis.
For volumes with pages loaded, OCR text is provided as an invisible overlay
on page images for selection and search.  Logged in users can annotate
text and image selections of page images, and can export an annotated
volume as TEI or a standalone `Jekyll <http://jekyllrb.com/>`_ website.

License
^^^^^^^

This software is distributed under the Apache 2.0 License.

Dependencies
^^^^^^^^^^^^

* SQL database for administration, collection banner images, annotation storage
* Fedora repository for access to digitized book content
* `Apache Solr <http://lucene.apache.org/solr/>`_ for browse by collection,
  search across all volumes, and search within a single volume
* `Python Social Auth <https://github.com/omab/python-social-auth>`_ for
  social authentication, and access to GitHub accounts for annotated
  volume export
* `IIIF <http://iiif.io/>`_ image server for page image content; e.g.
  `Loris <https://github.com/loris-imageserver/loris>`_
* `Annotator.js <http://annotatorjs.org/>`_ for annotation
* `teifacsimile-to-jekyll <https://github.com/emory-libraries-ecds/teifacsimile-to-jekyll>`_
  and `digitaledition-jekylltheme <https://github.com/emory-libraries-ecds/digitaledition-jekylltheme>`_
  for exporting annotated editions

Components
^^^^^^^^^^

``readux.collection``
    Models and views for access to collections, which are
    used to group digitized book content

``readux.books``
    Models and views for access to digizited book content; includes
    management commands for loading book covers and page content and
    generating page-level TEI facsimile

``readux.annotations``
    Django db models and views to provide an annotator-store backend;
    implements the `Annotator Core Storage api <http://docs.annotatorjs.org/en/v1.2.x/storage.html>`_.

``readux.pages``
    Functionality for site content such as an about page, annotation and export
    documentation, credits.  Powered by `FeinCMS <http://www.feincms.org/>`_.

