from django.contrib import admin

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.manifests.models import Manifest
from apps.iiif.kollections.models import Collection

class ManifestResource(resources.ModelResource):
    collectionid = fields.Field(
        column_name='collection',
        attribute='collection',
        widget=ForeignKeyWidget(Manifest, 'label'))
    class Meta:
        model = Manifest
        fields = ('uuid', 'pid', 'label','summary','author', 'published_city','published_date', 'publisher', 'pdf', 'metadata', 'viewingDirection', 'collectionid')


class ManifestAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = ManifestResource
    pass     
    list_display = ('uuid', 'pid', 'label', 'author', 'published_date', 'published_city', 'publisher', 'collection')
    
admin.site.register(Manifest, ManifestAdmin)