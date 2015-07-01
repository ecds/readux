:mod:`readux` Code Documentation
=================================

.. automodule:: readux


Collection
----------
.. automodule:: readux.collection
    :members:

Models
^^^^^^
.. automodule:: readux.collection.models
    :members:

Views
^^^^^^
.. automodule:: readux.collection.views
    :members:


Books
-----
.. automodule:: readux.books
    :members:

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

Manage Commands
^^^^^^^^^^^^^^^

.. automodule:: readux.books.management.page_import
    :members:

Custom manage commands
----------------------
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

DynDZI
------
.. automodule:: readux.dyndzi
    :members:

Models
^^^^^^
.. automodule:: readux.dyndzi.models
    :members:

Views
^^^^^^
.. automodule:: readux.dyndzi.views
    :members:

Fedora
^^^^^^
.. automodule:: readux.fedora
    :members:

Utilities
---------
.. automodule:: readux.utils
    :members:


Annotation
----------
.. automodule:: readux.annotations
    :members:

Models
^^^^^^
.. automodule:: readux.annotations.models
    :members:

Views
^^^^^^
.. automodule:: readux.annotations.views
    :members:
