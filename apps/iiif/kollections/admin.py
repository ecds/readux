from django.contrib import admin

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.kollections.models import Collection


class CollectionResource(resources.ModelResource):
    class Meta:
        model = Collection
        fields = ('id', 'label','summary', 'pid','metadata', 'upload')

class CollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = CollectionResource
    pass     
    list_display = ('id', 'pid', 'metadata', 'summary', 'label')
    
admin.site.register(Collection, CollectionAdmin)