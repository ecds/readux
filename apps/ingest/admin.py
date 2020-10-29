"""[summary]"""
from django.contrib import admin
from django.shortcuts import redirect
from .models import Local

class LocalAdmin(admin.ModelAdmin):
    """Django admin manifest resource."""
    fields = ('bundle', 'image_server')
    show_save_and_add_another = False

    def save_model(self, request, obj, form, change):
        obj.save()
        obj.refresh_from_db()
        obj.add_canvases()
        super().save_model(request, obj, form, change)
        # obj.refresh_from_db()
        # return redirect('apps.iiif.manifests_change', obj.manifest.id)

    def response_add(self, request, obj, post_url_continue=None):
        manifest_id = obj.manifest.id
        obj.delete()
        return redirect('/admin/manifests/manifest/{m}/change/'.format(m=manifest_id))

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Local

admin.site.register(Local, LocalAdmin)
