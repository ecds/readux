"""
Django admin module for Canvases
"""
from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from ..manifests.models import Manifest
from .models import Canvas
from .tasks import add_ocr

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

    def save_model(self, request, obj, form, change):
        obj.save()
        obj.refresh_from_db()
        add_ocr(obj.id, verbose_name=f'Creating OCR for {obj.manifest.pid} page {obj.position}')
        super().save_model(request, obj, form, change)

admin.site.register(Canvas, CanvasAdmin)
