from django.contrib import admin

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.manifests.models import Manifest, Note
from apps.iiif.kollections.models import Collection

class ManifestResource(resources.ModelResource):
    collectionid = fields.Field(
        column_name='collection',
        attribute='collection',
        widget=ForeignKeyWidget(Collection, 'label'))
    class Meta:
        model = Manifest
        import_id_fields = ('id',)
        fields = ('id', 'pid', 'label','summary','author', 'published_city','published_date', 'publisher', 'pdf', 'metadata', 'viewingDirection', 'collectionid')


class ManifestAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = ManifestResource
    pass     
    list_display = ('id', 'pid', 'label', 'author', 'published_date', 'published_city', 'publisher', 'collection')
    
class NoteAdmin(admin.ModelAdmin):
    class Meta:
        model = Note
        
admin.site.register(Manifest, ManifestAdmin)
admin.site.register(Note, NoteAdmin)