import datetime
from django.conf import settings
import os

from eulfedora.views import datastream_etag
from eulfedora.server import Repository, RequestFailed

from readux.books.models import Volume, VolumeV1_0, Page
from readux.utils import solr_interface, md5sum

'''
Conditional methods for calculating last modified time and ETags
for view methods in :mod:`readux.books.views`.

.. Note::

  In many cases, the Solr indexing timestamp is used rather than the object
  modification time, as this may account for changes to the site or indexing
  (including adding pages to a volume that is otherwise unchanged).
'''


def volumes_modified(request):
    'last modification time for all volumes'
    solr = solr_interface()
    results = solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL) \
                  .sort_by('-timestamp').field_limit('timestamp')
    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified
    if results.count():
        return results[0]['timestamp']

def volume_modified(request, pid):
    'last modification time for a single volume'
    solr = solr_interface()
    results = solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL,
                         pid=pid) \
                  .sort_by('-timestamp').field_limit('timestamp')
    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified,
    # and index timestamp for a volume will be updated when pages are added
    if results.count():
        return results[0]['timestamp']


def volume_pages_modified(request, pid):
    'last modification time for a single volume or its pages'
    solr = solr_interface()
    repo = Repository()
    vol = repo.get_object(pid, type=Volume)
    results = solr.query((solr.Q(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL) & solr.Q(pid=pid)) | \
                         (solr.Q(content_model=Page.PAGE_CONTENT_MODEL) & solr.Q(isConstituentOf=vol.uri))) \
                  .sort_by('-timestamp').field_limit('timestamp')
    # NOTE: using solr indexing timestamp instead of object last modified, since
    # if an object's index has changed it may have been modified,
    # and index timestamp for a volume will be updated when pages are added
    if results.count():
        return results[0]['timestamp']

def page_modified(request, pid):
    'last modification time for a single page'
    solr = solr_interface()
    results = solr.query(content_model=Page.PAGE_CONTENT_MODEL,
                         pid=pid) \
                  .sort_by('-timestamp').field_limit('timestamp')
    if results.count():
        return results[0]['timestamp']

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
    return datastream_etag(request, pid, Volume.ocr.id)

def ocr_lastmodified(request, pid):
    'last modified for Volume OCR datastream'
    return datastream_lastmodified(request, pid, Volume.ocr.id, Volume)

def page_image_etag(request, pid, **kwargs):
    'etag for Page image datastream'
    return datastream_etag(request, pid, Page.image.id, type=Page)

def page_image_lastmodified(request, pid, **kwargs):
    'last modified for Page image datastream'
    return datastream_lastmodified(request, pid, Page.image.id, type=Page)

