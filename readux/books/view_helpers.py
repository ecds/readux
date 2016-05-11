import datetime
from django.conf import settings
from django.utils import timezone
import os

from eulfedora.views import datastream_etag
from eulfedora.server import Repository
from eulfedora.util import RequestFailed

from readux.annotations.models import Annotation
from readux.books.models import Volume, VolumeV1_0, Page, PageV1_0
from readux.utils import solr_interface, md5sum

'''
Conditional methods for calculating last modified time and ETags
for view methods in :mod:`readux.books.views`.

.. Note::

  In many cases, the Solr indexing timestamp is used rather than the object
  modification time, as this may account for changes to the site or indexing
  (including adding pages to a volume that is otherwise unchanged).
'''


def volumes_modified(request, *args, **kwargs):
    'last modification time for all volumes'
    solr = solr_interface()
    results = solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL) \
                  .sort_by('-timestamp').field_limit('timestamp')
    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified

    # if user is logged in, changes in annotation totals result
    # in volume page display modifications
    latest_note = None
    if request.user.is_authenticated():
        latest_note = Annotation.objects.visible_to(request.user) \
                                .last_created_time()

    solrtime = results[0]['timestamp'] if results.count() else None
    return solrtimestamp_or_datetime(solrtime, latest_note)


def volume_modified(request, pid):
    'last modification time for a single volume'
    solr = solr_interface()
    results = solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL,
                         pid=pid) \
                  .sort_by('-timestamp').field_limit('timestamp')
    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified,
    # and index timestamp for a volume will be updated when pages are added

    # if a user is logged in, page should show as modified
    # when annotation count changes
    latest_note = None
    if request.user.is_authenticated():
        # NOTE: shouldn't be very expensive to init volume here; not actually
        # making any api calls, just using volume to get volume
        # uri and associated annotations
        repo = Repository()
        vol = repo.get_object(pid, type=Volume)
        # newest annotation creation for pages in this volume
        latest_note = vol.annotations().visible_to(request.user) \
                         .last_created_time()

    solrtime = results[0]['timestamp'] if results.count() else None
    return solrtimestamp_or_datetime(solrtime, latest_note)


def volume_pages_modified(request, pid):
    '''Last modification time for a single volume or its pages, or for
    any annotations of those pages.'''
    solr = solr_interface()
    repo = Repository()
    vol = repo.get_object(pid, type=Volume)

    # NOTE: some overlap with Volume find_solr_pages method...
    results = solr.query((solr.Q(content_model=Volume.VOLUME_CMODEL_PATTERN) & solr.Q(pid=pid)) | \
                         (solr.Q(content_model=Page.PAGE_CMODEL_PATTERN) & solr.Q(isConstituentOf=vol.uri))) \
                  .sort_by('-timestamp').field_limit('timestamp')

    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified,
    # and index timestamp for a volume will be updated when pages are added

    # Page could also be modified based on annotations of the pages.
    # We only show total counts per page, so might not be modified if the
    # total number has not changed, but simplest just to get last modification
    # date in case of changes.
    # Note that this does NOT account for annotation deletions.

    # if a user is logged in, page should show as modified
    # based on annotations
    # Only displaying annotation *count* so creation time should
    # be sufficient. (Does not take into account deletions...)
    latest_note = None
    if request.user.is_authenticated():
        # get annotations for pages in this volume
        try:
            latest_note = vol.annotations().visible_to(request.user) \
                             .last_created_time()
        except Annotation.DoesNotExist:
            # no notes for this volume
            pass

    solrtime = results[0]['timestamp'] if results.count() else None
    return solrtimestamp_or_datetime(solrtime, latest_note)


def page_modified(request, vol_pid, pid):
    'last modification time for a single page'
    solr = solr_interface()
    # TODO: use volume pid in query
    results = solr.query(content_model=PageV1_0.PAGE_CONTENT_MODEL,
                         pid=pid) \
                  .sort_by('-timestamp').field_limit('timestamp')

    # if user is logged in, page should show as modified
    # when annotations have changed
    latest_note = None
    if request.user.is_authenticated():
        # last update for annotations on this volume, if any
        repo = Repository()
        page = repo.get_object(pid, type=Page)
        latest_note = page.annotations().visible_to(request.user) \
                          .last_updated_time()

    solrtime = results[0]['timestamp'] if results.count() else None
    return solrtimestamp_or_datetime(solrtime, latest_note)


def solrtimestamp_or_datetime(solrtime, othertime):
    # Compare and return the more recent of a solr timestamp or an
    # annotation datetime.

    # convert solr timestamp to timezone-aware for comparison;
    # return the most recent of the two
    # FIXME:  assuming solr stores as UTC, confirm this
    if solrtime is not None and othertime is not None:
        solrtime = timezone.make_aware(solrtime, timezone.utc)
        return max(solrtime, othertime)

    # if both are not set, return solr time if present
    if solrtime is not None:
        return solrtime

    # if nothing has been returned, return other time (could be None)
    return othertime


books_models_filename = os.path.join(settings.BASE_DIR, 'readux', 'books', 'models.py')
books_models_modified = datetime.datetime.fromtimestamp(os.path.getmtime(books_models_filename))
books_models_md5sum = md5sum(books_models_filename)

def unapi_modified(request):
    'last-modification time for unapi; format list or metadata for a single item'
    item_id = request.GET.get('id', None)

    # if no id, just lists available formats
    if item_id is None:
        # configuration is based on Volume class definition, so should only
        # change if the file has changed
        return books_models_modified

    # metadata for a specific record
    else:
        return volume_modified(request, item_id)

def unapi_etag(request):
    'etag for unapi'
    item_id = request.GET.get('id', None)

    # if no id, just lists available formats
    if item_id is None:
        # configuration is based on Volume class definition, so should only
        # change if the file has changed
        return books_models_md5sum

    # metadata for a specific record
    else:
        fmt = request.GET.get('format', None)
        if fmt == 'rdf_dc':
            return datastream_etag(request, item_id, Volume.dc.id, type=Volume)


def datastream_lastmodified(request, pid, dsid, type):
    repo = Repository()
    try:
        obj = repo.get_object(pid, type=type)
        ds = obj.getDatastreamObject(dsid)
        if ds and ds.exists:
            return ds.created
    except RequestFailed:
        pass

def pdf_etag(request, pid):
    'etag for Volume PDF datastream'
    return datastream_etag(request, pid, Volume.pdf.id)

def pdf_lastmodified(request, pid):
    'last modified for Volume PDF datastream'
    return datastream_lastmodified(request, pid, Volume.pdf.id, Volume)

def ocr_etag(request, pid):
    'etag for Volume OCR datastream'
    return datastream_etag(request, pid, VolumeV1_0.ocr.id)

def ocr_lastmodified(request, pid):
    'last modified for Volume OCR datastream'
    return datastream_lastmodified(request, pid, VolumeV1_0.ocr.id, Volume)

# TODO: consider full text etag/lastmodified methods that would work
# for both volume v1.0 and v1.1; if v1.0, simple returns ocr methods
# above; otherwise, no etag is available but last-modified could be pulled
# from most recent solr indexed page.
# (If this requires additional fedora api calls to determine type,
# may be too costly.)

def page_image_etag(request, pid, **kwargs):
    'etag for Page image datastream'
    return datastream_etag(request, pid, Page.image.id, type=Page)

def page_image_lastmodified(request, pid, **kwargs):
    'last modified for Page image datastream'
    return datastream_lastmodified(request, pid, Page.image.id, type=Page)

