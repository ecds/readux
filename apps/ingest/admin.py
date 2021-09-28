"""[summary]"""
import logging
from mimetypes import guess_type
from os import environ, path, remove, listdir, rmdir
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django_celery_results.models import TaskResult
from apps.ingest import tasks
from apps.ingest.storages import IngestStorage
from .models import Bulk, IngestTaskWatcher, Local, Remote
from .services import clean_metadata, create_manifest, get_associated_meta, get_metadata_from
from .forms import BulkVolumeUploadForm

LOGGER = logging.getLogger(__name__)
class LocalAdmin(admin.ModelAdmin):
    """Django admin ingest.models.local resource."""
    fields = ('bundle', 'image_server')
    show_save_and_add_another = False

    def save_model(self, request, obj, form, change):
        obj.save()
        obj.manifest = create_manifest(obj)
        obj.save()
        obj.refresh_from_db()
        super().save_model(request, obj, form, change)
        if environ['DJANGO_ENV'] != 'test':
            local_task_id = tasks.create_canvas_form_local_task.delay(obj.id)
            local_task_result = TaskResult(task_id=local_task_id)
            local_task_result.save()
            file = request.FILES['bundle']
            IngestTaskWatcher.manager.create_watcher(
                task_id=local_task_id,
                task_result=local_task_result,
                task_creator=request.user,
                filename=file.name
            )

    def response_add(self, request, obj, post_url_continue=None):
        obj.refresh_from_db()
        manifest_id = obj.manifest.id
        return redirect('/admin/manifests/manifest/{m}/change/'.format(m=manifest_id))

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Local

class RemoteAdmin(admin.ModelAdmin):
    """Django admin ingest.models.remote resource."""
    fields = ('remote_url',)
    show_save_and_add_another = False

    def save_model(self, request, obj, form, change):
        obj.manifest = create_manifest(obj)
        obj.save()
        obj.refresh_from_db()
        super().save_model(request, obj, form, change)
        if environ['DJANGO_ENV'] != 'test':
            remote_task_id = tasks.create_remote_canvases.delay(obj.id)
            remote_task_result = TaskResult(task_id=remote_task_id)
            remote_task_result.save()
            IngestTaskWatcher.manager.create_watcher(
                task_id=remote_task_id,
                task_result=remote_task_result,
                task_creator=request.user,
                filename=obj.remote_url
            )

    def response_add(self, request, obj, post_url_continue=None):
        obj.refresh_from_db()
        manifest_id = obj.manifest.id
        return redirect('/admin/manifests/manifest/{m}/change/'.format(m=manifest_id))

class BulkAdmin(admin.ModelAdmin):
    """Django admin ingest.models.bulk resource."""

    form = BulkVolumeUploadForm

    def save_model(self, request, obj, form, change):
        form.storage = IngestStorage()
        obj.save()
        # Get files from multi upload form
        files = request.FILES.getlist("volume_files")
        # Find the metadata file and load it into list of dicts
        all_metadata = get_metadata_from(files)
        for file in files:
            # Skip metadata file now
            if 'metadata' in file.name.casefold() and 'zip' not in guess_type(file.name)[0]:
                continue
            # Associate metadata with zipfile
            if all_metadata is not None:
                file_meta = clean_metadata(get_associated_meta(all_metadata, file))
            else:
                file_meta = {}
            # Save in storage
            bundle_path = form.storage.save(
                path.join("bulk", str(obj.id), file.name), file
            )
            # Create local
            new_local = Local.objects.create(
                bulk=obj, bundle=bundle_path, image_server=obj.image_server, metadata=file_meta
            )
            if environ["DJANGO_ENV"] != "test":
                local_task_id = tasks.create_canvas_form_local_task.delay(new_local.id)
                local_task_result = TaskResult(task_id=local_task_id)
                local_task_result.save()
                IngestTaskWatcher.manager.create_watcher(
                    task_id=local_task_id,
                    task_result=local_task_result,
                    task_creator=request.user,
                    filename=file.name
                )
        obj.refresh_from_db()
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        # Delete local file
        file_path = obj.volume_files.path
        if path.isfile(file_path):
            remove(file_path)
        dir_path = file_path[0:file_path.rindex('/')]
        if len(listdir(dir_path)) == 0:
            rmdir(dir_path)
        obj.delete()
        return redirect("/admin/manifests/manifest/?o=-4")

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Bulk

class TaskWatcherAdmin(admin.ModelAdmin):
    """Django admin for ingest.models.IngestTaskWatcher resource."""

    list_display = (
        "id",
        "filename",
        "task_name",
        "task_status",
        "task_creator",
        "date_created",
        "date_done",
    )
    fields = (
        "id",
        "filename",
        "task_name",
        "task_status",
        "task_creator",
        "date_created",
        "date_done",
    )
    list_filter = ('task_creator',)
    date_hierarchy = 'task_result__date_created'
    empty_value_display = '(none)'

    def task_status(self, obj):
        """ Returns the task result with a link to view its details """
        if obj.task_result:
            url = reverse('admin:%s_%s_change' % (
                obj.task_result._meta.app_label,
                obj.task_result._meta.model_name
            ),  args=[obj.task_result.id] )
            return format_html(
                "<a href=\"{url}\">{label}</a>",
                url=url,
                label=obj.task_result.status
            )
        return None
    task_status.admin_order_field = 'task_result__status'

    def task_name(self, obj):
        """ Returns the task name for this task """
        if obj.task_result:
            return obj.task_result.task_name
        return None
    task_name.admin_order_field = 'task_result__task_name'

    def date_created(self, obj):
        """ Returns the creation date for this task """
        if obj.task_result:
            return obj.task_result.date_created
        return None
    date_created.admin_order_field = 'task_result__date_created'

    def date_done(self, obj):
        """ Returns the finished date for this task """
        if obj.task_result:
            return obj.task_result.date_done
        return None
    date_done.admin_order_field = 'task_result__date_done'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(Local, LocalAdmin)
admin.site.register(Remote, RemoteAdmin)
admin.site.register(Bulk, BulkAdmin)
admin.site.register(IngestTaskWatcher, TaskWatcherAdmin)
