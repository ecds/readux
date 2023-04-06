from traceback import format_tb
from django.urls.base import reverse
from django.template.loader import get_template
from django.conf import settings
from django.core.mail import send_mail

def send_email_on_failure(task_watcher=None, exception=None, traceback=None):
    """Function to send an email on task failure signal from Celery.

    :param task_watcher: The task watcher object
    :type task_watcher: app.ingest.models.TaskWatcher
    :param exception: Exception instance raised
    :type exception: Exception
    :param traceback: Stack trace object
    :type traceback: traceback
    """
    context = {}
    if task_watcher is not None:
        context['filename'] = task_watcher.filename
    if exception is not None:
        context['exception'] = exception.__repr__()
    if traceback is not None:
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
    if task_watcher is not None and task_watcher.task_creator is not None:
        send_mail(
            '[Readux] Failed: Ingest ' + task_watcher.filename,
            text_email,
            settings.READUX_EMAIL_SENDER,
            [task_watcher.task_creator.email],
            fail_silently=False,
            html_message=html_email
        )

def send_email_on_success(task_watcher=None):
    context = {}
    if task_watcher is not None:
        context['filename'] = task_watcher.filename
    if task_watcher is not None and task_watcher.associated_manifest is not None:
        context['manifest_url'] = settings.HOSTNAME + reverse(
            'admin:manifests_manifest_change', args=(task_watcher.associated_manifest.id,)
        )
        context['manifest_pid'] = task_watcher.associated_manifest.pid
        context['volume_url'] = task_watcher.associated_manifest.get_volume_url()
    else:
        context['manifests_list_url'] = settings.HOSTNAME + reverse(
            'admin:manifests_manifest_changelist'
        )
    html_email = get_template('ingest_success_email.html').render(context)
    text_email = get_template('ingest_success_email.txt').render(context)
    if task_watcher is not None and task_watcher.task_creator is not None:
        send_mail(
            '[Readux] Ingest complete: ' + task_watcher.filename,
            text_email,
            settings.READUX_EMAIL_SENDER,
            [task_watcher.task_creator.email],
            fail_silently=False,
            html_message=html_email
        )