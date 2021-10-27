# pylint: disable = unused-argument

""" Common tasks for ingest. """
import logging
from celery import Celery
from celery.signals import task_success, task_failure
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django_celery_results.models import TaskResult
from apps.ingest.models import IngestTaskWatcher
from .services import create_manifest
from .mail import send_email_on_failure, send_email_on_success

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

app = Celery('apps.ingest', result_extended=True)
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(name='creating_canvases_from_local', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
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
    # Sometimes, the IIIF server is not ready to process the image by the time the canvas is saved to
    # the database. As a double check loop through to make sure the height and width has been saved.
    for canvas in local_ingest.manifest.canvas_set.all():
        if canvas.width == 0 or canvas.height == 0:
            canvas.save()

@app.task(name='creating_canvases_from_remote', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
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

@app.task(name='uploading_to_s3', autoretry_for=(Exception,), retry_backoff=True, max_retries=20)
def upload_to_s3_task(local_id):
    """Task to create Canavs objects from remote IIIF manifest

    :param local_id: Primary key for .models.Local object
    :type local_id: UUID
    """
    local = Local.objects.get(pk=local_id)

    # Upload tempfile to S3
    local.bundle_to_s3()

    # Create manifest now that we have a file
    if local.manifest is None:
        local.manifest = create_manifest(local)

    # Queue task to create canvases etc.
    local.save()
    local.refresh_from_db()
    local_task_id = create_canvas_form_local_task.delay(local_id)
    local_task_result = TaskResult(task_id=local_task_id)
    local_task_result.save()
    IngestTaskWatcher.manager.create_watcher(
        task_id=local_task_id,
        task_result=local_task_result,
        task_creator=get_user_model().objects.get(pk=local.creator.id),
        associated_manifest=local.manifest,
        filename=local.bundle.name
    )

@task_failure.connect
def send_email_on_failure_task(sender=None, exception=None, task_id=None, traceback=None, *args, **kwargs):
    """Function to send an email on task success signal from Celery.

    :param sender: The task object
    :type sender: celery.task
    """
    if sender is not None and 'creating_canvases_from_local' in sender.name:
        task_watcher = IngestTaskWatcher.manager.get(task_id=task_id)
        if task_watcher is not None:
            send_email_on_failure(task_watcher, exception, traceback, *args, **kwargs)

@task_success.connect
def send_email_on_success_task(sender=None, **kwargs):
    """Function to send an email on task success signal from Celery.

    :param sender: The task object
    :type sender: celery.task
    """
    if sender is not None and 'creating_canvases_from_local' in sender.name:
        task_id = sender.request.id
        task_watcher = IngestTaskWatcher.manager.get(task_id=task_id)
        if task_watcher is not None:
            send_email_on_success(task_watcher)
