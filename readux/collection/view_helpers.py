from readux.annotations.models import Annotation
from readux.utils import solr_interface
from readux.books.models import VolumeV1_0
from readux.books.view_helpers import solrtimestamp_or_datetime
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
                         solr.Q(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL)) \
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
                         solr.Q(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL,
                                collection_id=pid)) \
                  .sort_by('-timestamp').field_limit('timestamp')

    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified

    # if user is logged in, annotations modifications can result in
    # changes to the collection page display (annotation count)
    latest_note = None
    if request.user.is_authenticated():
        latest_note = Annotation.objects.visible_to(request.user) \
                                .last_created_time()

    solrtime = results[0]['timestamp'] if results.count() else None
    return solrtimestamp_or_datetime(solrtime, latest_note)
