"""
Django admin module for Canvases
"""
from os import environ
from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from ..manifests.documents import ManifestDocument
from ..manifests.models import Manifest
from .models import Canvas
from .tasks import add_ocr_task
from . import services

def resave_gethw_admin_action(modeladmin, request, queryset):
    """Re-run before_save()'s height/width fixup for each selected canvas.

    Calling canvas.save() per canvas would trigger a full-manifest
    Elasticsearch reindex per canvas (Canvas is a related_model of
    ManifestDocument) -- for a manifest with many pages selected at once
    that's an O(n^2) reindex storm. bulk_update() applies the recomputed
    fields directly, bypassing signals, then each distinct manifest touched
    is reindexed exactly once.
    """
    canvases = list(queryset)
    for canvas in canvases:
        canvas.before_save()
    Canvas.objects.bulk_update(
        canvases, ["width", "height", "position", "resource", "image_server"]
    )

    manifest_ids = {canvas.manifest_id for canvas in canvases if canvas.manifest_id}
    index = ManifestDocument()
    for manifest in Manifest.objects.filter(pk__in=manifest_ids):
        index.update(manifest, True, "index")
resave_gethw_admin_action.short_description = 'Resave for Height Width'

class CanvasResource(resources.ModelResource):
    """Django admin Canvas resource"""
    manifest_id = fields.Field(
        column_name='manifest',
        attribute='manifest',
        widget=ForeignKeyWidget(Manifest, 'pid')
    )

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Canvas
        fields = (
            'id', 'pid', 'position', 'height', 'width',
            'manifest_id',
            'label', 'summary', 'default_ocr', 'ocr_offset'
        )

class CanvasAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Django admin settings for Canvas."""
    resource_class = CanvasResource
    list_display = (
        'id', 'pid', 'height', 'width', 'position',
        'is_starting_page', 'manifest', 'label'
    )
    search_fields = (
        'pid', 'is_starting_page',
        'manifest__pid', 'manifest__label'
    )
    actions = (resave_gethw_admin_action, )

    def save_model(self, request, obj, form, change):
        obj.save()
        obj.refresh_from_db()
        super().save_model(request, obj, form, change)

        if environ['DJANGO_ENV'] == 'test':
            ocr = services.get_ocr(obj)
            if ocr is not None:
                services.add_ocr_annotations(obj, ocr)

        else:
            add_ocr_task.delay(obj.id)

admin.site.register(Canvas, CanvasAdmin)
