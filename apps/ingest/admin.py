"""[summary]"""
from os import path
from django.contrib import admin
from django.shortcuts import redirect
import apps.ingest.tasks as tasks
from .models import Local, Remote

class LocalAdmin(admin.ModelAdmin):
    """Django admin ingest.models.local resource."""
    fields = ('bundle', 'image_server')
    show_save_and_add_another = False

    def save_model(self, request, obj, form, change):
        obj.save()
        if path.isfile(obj.bundle.path):
            if obj.manifest is None:
                obj.manifest = tasks.create_manifest(obj)
            obj.refresh_from_db()
            tasks.create_canvas_task(obj.id)
            super().save_model(request, obj, form, change)
        else:
            return self.save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        if obj.manifest is not None:
            manifest_id = obj.manifest.id
            return redirect('/admin/manifests/manifest/{m}/change/'.format(m=manifest_id))
        else:
            obj.manifest = tasks.create_manifest(obj)
            return self.response_add(request, obj, post_url_continue)

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
