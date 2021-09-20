"""[summary]"""
import os
from apps.ingest.storages import IngestStorage
import logging
from os import environ, path
from django.contrib import admin
from django.shortcuts import redirect
import apps.ingest.tasks as tasks
from .models import Bulk, Local, Remote
from .services import create_manifest
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
            tasks.create_canvas_form_local_task.delay(obj.id)

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
            tasks.create_remote_canvases.delay(obj.id)

    def response_add(self, request, obj, post_url_continue=None):
        obj.refresh_from_db()
        manifest_id = obj.manifest.id
        return redirect('/admin/manifests/manifest/{m}/change/'.format(m=manifest_id))

class BulkAdmin(admin.ModelAdmin):
    form = BulkVolumeUploadForm

    def save_model(self, request, obj, form, change):
        form.storage = IngestStorage()
        obj.save()
        files = request.FILES.getlist('volume_files')
        for f in files:
            path = form.storage.save(os.path.join('bulk', str(obj.id), f.name), f)
            new_local = Local.objects.create(bulk=obj, bundle=path, image_server=obj.image_server)
            if environ['DJANGO_ENV'] != 'test':
                tasks.create_canvas_form_local_task.delay(new_local.id)
        obj.refresh_from_db()
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        obj.delete()
        return redirect('/admin/manifests/manifest/?o=-4')

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Bulk

admin.site.register(Local, LocalAdmin)
admin.site.register(Remote, RemoteAdmin)
admin.site.register(Bulk, BulkAdmin)
