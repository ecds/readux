"""[summary]"""
from os import path
from django.contrib import admin
from django.shortcuts import redirect
import apps.ingest.tasks as tasks
from .models import Bulk, Local, Remote, Volume
import logging

LOGGER = logging.getLogger(__name__)
class LocalAdmin(admin.ModelAdmin):
    """Django admin ingest.models.local resource."""
    fields = ('bundle', 'image_server')
    show_save_and_add_another = False

    def save_model(self, request, obj, form, change):
        obj.save()
        # if path.isfile(obj.bundle.path):
        obj.manifest = tasks.create_manifest(obj)
        obj.save()
        obj.refresh_from_db()
        super().save_model(request, obj, form, change)
        tasks.create_canvas_form_local_task.delay(obj.id)
        # else:
        #     return self.save_model(request, obj, form, change)

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
        obj.manifest = tasks.create_manifest(obj)
        obj.save()
        obj.refresh_from_db()
        tasks.create_remote_canvases(obj.id, verbose_name=f'Creating canvas {obj.pid} for {obj.manifest.id}')
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        obj.refresh_from_db()
        manifest_id = obj.manifest.id
        return redirect('/admin/manifests/manifest/{m}/change/'.format(m=manifest_id))

class VolumeInline(admin.StackedInline):
    model = Volume
    extra = 1

class BulkAdmin(admin.ModelAdmin):
    inlines = [VolumeInline]

    def save_model(self, request, obj, form, change):
        obj.save()

        for afile in request.FILES.getlist('photos_multiple'):
            Volume.objects.create(bulk_id=obj.id, volume_file=afile)

admin.site.register(Local, LocalAdmin)
admin.site.register(Remote, RemoteAdmin)
admin.site.register(Bulk, BulkAdmin)
