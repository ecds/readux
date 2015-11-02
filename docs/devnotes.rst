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

