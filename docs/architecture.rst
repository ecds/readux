Architecture
------------

.. _architecture-overview:

High-Level Architecture
^^^^^^^^^^^^^^^^^^^^^^^

The following diagram provides a high-level view of the Readux system
architecture.  The direction of arrows indicates the flow of data.

.. diagram of fedora/solr/eulindexer

.. graphviz:: diagrams/architecture.dot

Readux is a Django application running on a web server.  It uses a
SQL database for user accounts, collection banner images and annotations.
Collection and digitized book content is stored in a Fedora Commons
3.x repository and accessed using REST APIs with
`eulfedora <https://github.com/emory-libraries/eulfedora>`_.  In normal
operations, Readux does *not* ingest or modify content in Fedora (although
the codebase does currently include scripts for ingesting contents).

Readux uses `Loris IIIF Image Server <https://github.com/loris-imageserver/loris>`_
to serve out page image in various sizes and support deep zoom.  Loris is
configured to pull images from Fedora by URL.  Currently, Loris
is not directly exposed to users; Loris IIIF outputs are mediated through
the Readux application (although this is something that may be revisited).
The page image urls do matter: Readux image annotations reference the
image url, so changing urls will require updating existing annotations.  Using
more semantic image urls (thumbnail, page, full) within Readux *may* be a
more durable choice than exposing specific IIIF URLs with sizes hard-coded.

Readux uses `Apache Solr <http://lucene.apache.org/solr/>`_ for search
and browse functionality.  This includes:

- searching across all volumes (see :meth:`~readux.books.views.VolumeSearch`)
- searching within a single volume (see :meth:`~readux.books.views.VolumeDetail`)
- browsing volumes by collection (see :meth:`~readux.collection.views.CollectionDetail`
  or :meth:`~readux.collection.views.CollectionCoverDetail`)
- browsing pages within a volume (see :meth:`~readux.books.views.VolumePageList`)

We use `eulindexer <https://github.com/emory-libraries/eulindexer>`_ to
manage and update Fedora-based Solr indexes.  :mod:`eulindexer` loads the Solr
configuration from Readux and listens to the Fedora messaging queue for
updates.  When an update event occurs, :mod:`eulinedexer` queries Fedora
to determine the content type (based on content model), and then queries
the relevant application for the index data to be sent to Solr.  Readux
uses the :mod:`eulfedora.indexdata` views and extends the default
:meth:`eulfedora.models.DigitalObject.index_data` method to include
additional fields needed for Readux-specific functionality; see the code
for :meth:`readux.books.models.Volume.index_data` and
:meth:`readux.books.models.Page.index_data` for specifics.  The current
Solr schema is included in the ``deploy/solr`` directory.


.. _book-content-models:

Book Content Models
^^^^^^^^^^^^^^^^^^^

The following diagram shows how Readux digitized book content is
structured in Fedora.

.. diagram of book/volume/page model

.. graphviz:: diagrams/book_cmodels.dot


For consistency between single and  multi-volume works, every Volume is
associated with a Book.  The Book object contains the MARC XML metadata;
each Volume includes a PDF, and may include OCR XML.  For Volumes with
pages loaded, each page is stored as an individual object with a relation
to the parent volume.  Any volumes with a cover loaded will have at least
one page, with the special `hasPrimaryImage <http://pid.emory.edu/ns/2011/repo-management/#hasPrimaryImage>`_ relationship to indicate which page image should be used as the cover or for
thumbnails (this may or may not be the first page).  The book-level
object is not currently directly exposed in Readux, but it is used
to associate volumes with collections, and volumes from the same book
are linked as "related volumes" from each individual volume landing page.

Pages are ordered within a volume using a `pageOrder <http://pid.emory.edu/ns/2011/repo-management/#pageOrder>`_
property set in the RELS-EXT of each page.

For implementation specifics, see code documentation for:

   * :class:`readux.books.models.Book`
   * :class:`readux.books.models.Volume`
   * :class:`readux.books.models.Page`


.. _volume_page_variants:

Volume and Page variants
^^^^^^^^^^^^^^^^^^^^^^^^

Readux currently includes two different variants of
:class:`~readux.books.models.Volume` and
:class:`~readux.books.models.Page` objects.
The primary difference is that the ScannedVolume-1.0 objects contain
a single ABBYY OCR XML file with the OCR for the entire volume,
where the ScannedVolume-1.1 objects have no volume-level OCR,
but each page has a METS/ALTO OCR XML file, instead of the plain text OCR
content present in the ScannedPage-1.0 objects.

.. graphviz:: diagrams/volume_variants.dot

Readux uses TEI facsimile to provide a consistent format for positioned
OCR text data across these variations.  Readux includes scripts
and XSLT to generate TEI from the volume-level ABBYY OCR or the
page-level ALTO, and adds the TEI to the page object in Fedora.  In addition,
Readux adds xml ids to the original OCR XML, which is carried through
to the TEI and then the HTML displayed on the Readux site for annotation,
in order to ensure durability and correlation of content with annotations.


Fedora pids
^^^^^^^^^^^

Readux is intended for display and access, and not as a management tool.
However, for historical reasons it currently includes some scripts for
importing covers and pages, and also a preliminary script for importing
a new Volume-1.1 work with pages and metadata (see :ref:`import_volume`).
Prior to Readux, existing Emory Libraries digitized book content in the
repository only included Book and Volume records.  There are manage commands
to :ref:`import_covers` and :ref:`import_pages`, but the current implementation
uses a legacy Digitization Workflow (:mod:`readux.books.digwf`).

Following our standard practice, any objects ingested via Readux
have Archival Resource Keys (ARKs) generated via our
`PID manager application <https://github.com/emory-libraries/pidman>`_,
which are then used as the basis for Fedora object pids.  The ARK is stored
in the object metadata and displayed on the website as a permalink.





