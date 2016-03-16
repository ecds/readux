Books
-----
.. automodule:: readux.books
    :members:

.. diagram of book/volume/page model

Fedora Content Models
^^^^^^^^^^^^^^^^^^^^^

The following diagram shows how Readux digitized book content is
structured in Fedora.

.. graphviz::

    digraph {
        rankdir=RL;

        subgraph cluster_0 {
            style=invis;
            Volume2 -> Book[label="constituent", style=dashed];
            Volume -> Book[label="constituent"];
            Volume3 -> Book[label="constituent", style=dashed];

        }
        subgraph cluster_1 {
            color=lightgray;
            label="Pages";
            node [shape=box];
            Page1 -> Volume[label="constituent"];
            Page2 -> Volume[label="constituent"];
            Page3 -> Volume[label="constituent"];
        }

        Volume -> Page1[label="primary image"];
    }


For consistency between single and  multi-volume works, every Volume is
associated with a Book.  The Book object  contains the MARC XML metadata;
each Volume includes a PDF, and may include OCR XML.  For volumes with
pages loaded, each page is stored as an individual object with a relation
to the parent volume.  Any volumes with a cover loaded will have at least
one page, with the special custom "primary image" relationship to
indicate which page image should be used as the cover.  The book-level
object is not currently directly exposed in Readux, but it is used
to associate volumes with collections, and volumes from the same book
are linked as "related volumes" from the individual volume landing page.


Models
^^^^^^
.. automodule:: readux.books.models
    :members:

Views
^^^^^^
.. automodule:: readux.books.views
    :members:

DigWF
^^^^^^
.. automodule:: readux.books.digwf
    :members:

IIIF Client
^^^^^^^^^^^
.. automodule:: readux.books.iiif
    :members:

TEI
^^^
.. automodule:: readux.books.tei
    :members:

Annotate
^^^^^^^^
.. automodule:: readux.books.annotate
    :members:

Markdown to TEI
^^^^^^^^^^^^^^^
.. automodule:: readux.books.markdown_tei
    :members:

Export
^^^^^^
.. automodule:: readux.books.export
    :members:

GitHub
^^^^^^
.. automodule:: readux.books.github
    :undoc-members:
    :members:


Custom manage commands
^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: readux.books.management.page_import
    :members:


The following management commands are available.  For more details, use
``manage.py help <command>``.  As much as possible, all custom commands honor the
built-in django verbosity options.

* **import_covers**
    .. automodule:: readux.books.management.commands.import_covers
        :members:

* **import_pages**
    .. automodule:: readux.books.management.commands.import_pages
       :members:

* **update_arks**
    .. autoclass:: readux.books.management.commands.update_arks.Command
       :members:

