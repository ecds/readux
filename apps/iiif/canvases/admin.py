from django.contrib import admin

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.canvases.models import Canvas, IServer
from apps.iiif.manifests.models import Manifest

class CanvasResource(resources.ModelResource):
    manifestid = fields.Field(
        column_name='manifest',
        attribute='manifest',
        widget=ForeignKeyWidget(Manifest, 'pid'))
    IIIF_IMAGE_SERVER_BASElink = fields.Field(
        column_name='IIIF_IMAGE_SERVER_BASE',
        attribute='IIIF_IMAGE_SERVER_BASE',
        widget=ForeignKeyWidget(IServer, 'IIIF_IMAGE_SERVER_BASE'))
    class Meta:
        model = Canvas
        fields = ('id', 'pid', 'position','height','width', 'IIIF_IMAGE_SERVER_BASElink','manifestid', 'label', 'summary')

class CanvasAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = CanvasResource
    pass     
    list_display = ('id', 'pid', 'height', 'width', 'position', 'is_starting_page', 'manifest', 'label')
    
class IServerResource(resources.ModelResource):
    class Meta:
        model = IServer
        fields = ('id', 'IIIF_IMAGE_SERVER_BASE')

class IServerAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = IServerResource
    pass     
    list_display = ('IIIF_IMAGE_SERVER_BASE',)
    
admin.site.register(Canvas, CanvasAdmin)
admin.site.register(IServer, IServerAdmin)