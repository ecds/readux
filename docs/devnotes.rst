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

