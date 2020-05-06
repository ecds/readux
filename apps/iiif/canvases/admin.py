"""
Django admin module for Canvases
"""
from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import Canvas, IServer
from ..manifests.models import Manifest

class CanvasResource(resources.ModelResource):
    """Django admin Canvas resource"""
    manifest_id = fields.Field(
        column_name='manifest',
        attribute='manifest',
        widget=ForeignKeyWidget(Manifest, 'pid'))
    IIIF_IMAGE_SERVER_BASElink = fields.Field(
        column_name='IIIF_IMAGE_SERVER_BASE',
        attribute='IIIF_IMAGE_SERVER_BASE',
        widget=ForeignKeyWidget(IServer, 'IIIF_IMAGE_SERVER_BASE'))
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Canvas
        fields = (
            'id', 'pid', 'position', 'height', 'width',
            'IIIF_IMAGE_SERVER_BASElink', 'manifest_id',
            'label', 'summary', 'default_ocr'
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

class IServerResource(resources.ModelResource):
    """Django admin IServer resource."""
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = IServer
        fields = ('id', 'IIIF_IMAGE_SERVER_BASE')

class IServerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Django admin settings for IServer."""
    resource_class = IServerResource
    list_display = ('IIIF_IMAGE_SERVER_BASE',)

admin.site.register(Canvas, CanvasAdmin)
admin.site.register(IServer, IServerAdmin)
