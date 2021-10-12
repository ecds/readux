# pylint: disable = unused-argument

""" Common tasks for ingest. """
import logging
from traceback import format_tb
from celery import Celery
from celery.signals import task_success, task_failure
from django.apps import apps
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.urls.base import reverse
from apps.ingest.models import IngestTaskWatcher
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


@task_failure.connect
def send_email_on_failure(sender=None, exception=None, task_id=None, traceback=None, *args, **kwargs):
    """Function to send an email on task success signal from Celery.

    :param sender: The task object
    :type sender: celery.task
    """
    if 'creating_canvases_from_local' in sender.name:
        task_watcher = IngestTaskWatcher.manager.get(task_id=task_id)
        context = {}
        context['filename'] = task_watcher.filename
        context['exception'] = exception.__repr__()
        context['traceback'] = '\n'.join(format_tb(traceback))
        context['result_url'] = settings.HOSTNAME + reverse(
            "admin:%s_%s_change"
            % (
                task_watcher.task_result._meta.app_label,
                task_watcher.task_result._meta.model_name,
            ),
            args=[task_watcher.task_result.id],
        )
        html_email = get_template('ingest_failure_email.html').render(context)
        text_email = get_template('ingest_failure_email.txt').render(context)
        if task_watcher and task_watcher.task_creator and task_watcher.task_creator.email:
            send_mail(
                '[Readux] Ingest failed: ' + task_watcher.filename,
                text_email,
                settings.READUX_EMAIL_SENDER,
                [task_watcher.task_creator.email],
                fail_silently=False,
                html_message=html_email
            )

@task_success.connect
def send_email_on_success(sender=None, **kwargs):
    """Function to send an email on task success signal from Celery.

    :param sender: The task object
    :type sender: celery.task
    """
    if 'creating_canvases_from_local' in sender.name:
        task_id = sender.request.id
        task_watcher = IngestTaskWatcher.manager.get(task_id=task_id)
        context = {}
        context['filename'] = task_watcher.filename
        if task_watcher.associated_manifest:
            context['manifest_url'] = settings.HOSTNAME + reverse(
                'admin:manifests_manifest_change', args=(task_watcher.associated_manifest.id,)
            )
            context['manifest_pid'] = task_watcher.associated_manifest.pid
            context['volume_url'] = task_watcher.associated_manifest.get_absolute_url()
        else:
            context['manifests_list_url'] = settings.HOSTNAME + reverse(
                'admin:manifests_manifest_changelist'
            )
        html_email = get_template('ingest_success_email.html').render(context)
        text_email = get_template('ingest_success_email.txt').render(context)
        if task_watcher and task_watcher.task_creator and task_watcher.task_creator.email:
            send_mail(
                '[Readux] Ingest complete: ' + task_watcher.filename,
                text_email,
                settings.READUX_EMAIL_SENDER,
                [task_watcher.task_creator.email],
                fail_silently=False,
                html_message=html_email
            )
