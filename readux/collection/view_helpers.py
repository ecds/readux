from readux.utils import solr_interface
from readux.books.models import Volume
from readux.collection.models import Collection

'''
Conditional methods for calculating last modified time and ETags
for view methods in :mod:`readux.collection.views`.

.. Note::

  In many cases, the Solr indexing timestamp is used rather than the object
  modification time, as this may account for updates to the site or indexing.
'''


def collections_modified(request, *args, **kwargs):
    'Last modification time for list of all collections'
    # - collection browse includes collection information and volume counts,
    # so should be considered modified if any of those objects change

    # NOTE: this does not take into account changes in images for collections,
    # as there is currently no good way to determine the last-modification
    # date for a collection image
    solr = solr_interface()
    results = solr.query(solr.Q(solr.Q(content_model=Collection.COLLECTION_CONTENT_MODEL) &
                                solr.Q(owner='LSDI-project')) | \
                         solr.Q(content_model=Volume.VOLUME_CONTENT_MODEL)) \
                  .sort_by('-timestamp').field_limit('timestamp')
    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified
    if results.count():
        return results[0]['timestamp']


def collection_modified(request, pid, **kwargs):
    '''last modification time for single collection view.
     Includes collection information and volumes in the collection,
     so should be considered modified if any of those objects change.
     Does *not* take into account changes in collection image via Django admin.
     '''
    solr = solr_interface()
    results = solr.query(solr.Q(pid=pid) | \
                         solr.Q(content_model=Volume.VOLUME_CONTENT_MODEL,
                                collection_id=pid)) \
                  .sort_by('-timestamp').field_limit('timestamp')

    print '*** debug: col mod results are = ', results
    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified
    if results.count():
        return results[0]['timestamp']
