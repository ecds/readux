Books
-----

.. contents:: Contents
    :local:
    :depth: 2

.. automodule:: readux.books
    :members:

For more information on the Fedora content modeling and object
relations, see :ref:`book-content-models` and :ref:`volume_page_variants`.


Models
^^^^^^
.. automodule:: readux.books.models
    :members:

Views
^^^^^^
.. automodule:: readux.books.views
    :members:

DigWF
^^^^^
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

.. _import_covers:

import_covers
~~~~~~~~~~~~~
    .. automodule:: readux.books.management.commands.import_covers
        :members:

.. _import_pages:

import_pages
~~~~~~~~~~~~

    .. automodule:: readux.books.management.commands.import_pages
       :members:

update_arks
~~~~~~~~~~~
    .. autoclass:: readux.books.management.commands.update_arks.Command
       :members:

.. _import_volume:

import_volume
~~~~~~~~~~~~~
    .. automodule:: readux.books.management.commands.import_volume
       :members:
