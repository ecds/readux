# pylint: disable = unused-argument

""" Common tasks for ingest. """
import logging
from celery import Celery
from django.apps import apps
from django.conf import settings
from .services import create_manifest

# Use `apps.get_model` to avoid circular import error. Because the parameters used to
# create a background task have to be serializable, we can't just pass in the model object.
Local = apps.get_model('ingest.local') # pylint: disable = invalid-name
Remote = apps.get_model('ingest.remote')

LOGGER = logging.getLogger(__name__)
logging.getLogger("background_task").setLevel(logging.ERROR)
logging.getLogger('boto3').setLevel(logging.ERROR)
logging.getLogger('botocore').setLevel(logging.ERROR)
logging.getLogger('s3transfer').setLevel(logging.ERROR)
logging.getLogger('factory').setLevel(logging.ERROR)

app = Celery('apps.ingest')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(name='creating_canvases_from_local', autoretry_for=(Local.DoesNotExist,), retry_backoff=5)
def create_canvas_form_local_task(ingest_id):
    """Background task to create canvases and upload images.

    :param ingest_id: Primary key for .models.Local object
    :type ingest_id: UUID

    """
    local_ingest = Local.objects.get(pk=ingest_id)

    if local_ingest.manifest is None:
        local_ingest.manifest = create_manifest(local_ingest)
        local_ingest.save()
        local_ingest.refresh_from_db()

    local_ingest.create_canvases()

@app.task(name='creating_canvases_from_remote', autoretry_for=(Remote.DoesNotExist,), retry_backoff=5)
def create_remote_canvases(ingest_id, *args, **kwargs):
    """Task to create Canavs objects from remote IIIF manifest

    :param ingest_id: Primary key for .models.Remote object
    :type ingest: UUID
    """
    remote_ingest = Remote.objects.get(pk=ingest_id)

    if remote_ingest.manifest is None:
        remote_ingest.manifest = create_manifest(remote_ingest)
        remote_ingest.save()
        remote_ingest.refresh_from_db()

    remote_ingest.create_canvases()
