"""[summary]"""
from django.contrib import admin
from django.shortcuts import redirect
import apps.ingest.services as services
import apps.ingest.tasks as tasks
from .models import Local, Remote

class LocalAdmin(admin.ModelAdmin):
    """Django admin ingest.models.local resource."""
    fields = ('bundle', 'image_server')
    show_save_and_add_another = False

    def save_model(self, request, obj, form, change):
        if obj.manifest is None:
            obj.manifest = tasks.create_manifest(obj)
        obj.save()
        obj.refresh_from_db()
        tasks.create_canvas_task(obj.id)
        super().save_model(request, obj, form, change)
        # obj.refresh_from_db()
        # return redirect('apps.iiif.manifests_change', obj.manifest.id)

    def response_add(self, request, obj, post_url_continue=None):
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
        # manifest.save()
        obj.save()
        obj.refresh_from_db()
        tasks.create_remote_canvases(obj.id)
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        obj.refresh_from_db()
        manifest_id = obj.manifest.id
        return redirect('/admin/manifests/manifest/{m}/change/'.format(m=manifest_id))

admin.site.register(Local, LocalAdmin)
admin.site.register(Remote, RemoteAdmin)
