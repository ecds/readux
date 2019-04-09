from django.contrib import admin

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.manifests.models import Manifest, Note
from apps.iiif.canvases.models import Canvas
from apps.iiif.kollections.models import Collection

class ManifestResource(resources.ModelResource):
    collectionid = fields.Field(
        column_name='collections',
        attribute='collections',
        widget=ManyToManyWidget(Collection, field='label'))
    class Meta:
        model = Manifest
        import_id_fields = ('id',)
        fields = ('id', 'pid', 'label','summary','author', 'published_city','published_date', 'publisher', 'pdf', 'metadata', 'viewingDirection', 'collectionid')


class ManifestAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = ManifestResource
    pass     
    filter_horizontal = ('collections',)
    list_display = ('id', 'pid', 'label', 'author', 'published_date', 'published_city', 'publisher')
    search_fields = ('label','author','published_date')

    
class NoteAdmin(admin.ModelAdmin):
    class Meta:
        model = Note
        
admin.site.register(Manifest, ManifestAdmin)
admin.site.register(Note, NoteAdmin)