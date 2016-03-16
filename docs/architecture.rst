Architecture
------------

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







