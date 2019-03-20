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
    class Meta:
        model = Canvas
        import_id_fields = ['uuid']
        fields = ('uuid', 'pid', 'position','height','width', 'IIIF_IMAGE_SERVER_BASE','manifestid', 'label', 'summary')

class CanvasAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = CanvasResource
    pass     
    list_display = ('uuid', 'pid', 'height', 'width', 'position', 'manifest', 'label')
    
class IServerAdmin(admin.ModelAdmin):
    list_display = ('IIIF_IMAGE_SERVER_BASE',)
    
admin.site.register(Canvas, CanvasAdmin)
admin.site.register(IServer, IServerAdmin)