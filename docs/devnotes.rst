.. _DEVNOTES:

DEVELOPER NOTES
===============

Useful Queries
--------------

Find Volume objects in Fedora that do *not* have a cover image:

.. code-block:: sparql

    SELECT ?pid
    WHERE {
        ?pid <fedora-model:hasModel> <info:fedora/emory-control:ScannedVolume-1.0> .
        OPTIONAL {
            ?pid <http://pid.emory.edu/ns/2011/repo-management/#hasPrimaryImage> ?img
        }
        FILTER (!BOUND(?img))
    }

.. Note::
   Because Fedora's RISearch currently only supports SPARQL 1.0, this
   query requires the optional/not bound filter rather than the more
   straightforward NOT EXISTS that is supported in SPARQL 1.1+.

Other tasks
-----------

Remove post-1922 yearbooks from the Solr index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start up a django python shell (``python manage.py shell``) and do
the following::

```
from readux.utils import solr_interface
from readux.books.models import VolumeV1_0, SolrVolume
solr = solr_interface()
vols = solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL, collection_id='emory-control:LSDI-EmoryYearbooks').results_as(SolrVolume)
solr.delete([{'pid': vol['pid']} for vol in vols if int(vol.volume[:4]) >= 1923])
solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL, collection_id='emory-control:LSDI-EmoryYearbooks').count()
```

Sync volume content and annotations between instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

How to sync a volume with all its related content (relevant book and page
objects in Fedora) along with a set of annotations between two
environments, e.g. between production and QA.

In the source installation of Readux (e.g. production), use the
``find_test_pids`` script to get a list of volume, book, and page pids.
This reequires an input file, so create a file with a list of pids, one
per line (only one line if you are only synchronizing one volume)::

  echo "pid" > /tmp/vol_pid.txt
  python manage.py find_test_pids /tmp/vol_pid.txt > /tmp/vol_all_pids.txt

Use the eulfedora repo-cp script to sync the data between Fedora repositories
using the list of pids you generated::

  repo-cp prod qa --file /tmp/vol_all_pids.txt


Use the annotations api from your source installation to find the annotations
associated with your volume, e.g.:

  http://readux.library.emory.edu/annotations/api/search?user=<username>

or (eventually, but not supported in readux 1.3)::

  http://readux.library.emory.edu/annotations/api/search?volume_uri=http://readux.library.emory.edu/books/pid:###/

Save annotations as JSON and replace the base source urls with
destination site urls  (e.g., readux.library to testreadux.library, but
note that this *must* match the url configured in your Django sites,
so if you are using a proxy use that url).  Then import the annotations
into your destination readux instance::

  python manage.py import_annotations my_annotations.json

Note that this requires equivalent user accounts to exist in both instances
(and if a different user happened to have the same username in the second
location, you have just given them access to another person's annotations).





