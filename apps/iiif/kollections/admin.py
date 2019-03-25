from django.contrib import admin

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.models import Manifest, Note


class CollectionResource(resources.ModelResource):
    class Meta:
        model = Collection
        fields = ('id', 'label','summary', 'pid','metadata', 'upload')

class ManifestInline(admin.TabularInline):
    model = Manifest.collections.through
    readonly_fields = ('manifest_label',)

    def manifest_label(self, instance):
        return instance.manifest.label
    manifest_label.short_description = 'Manifest title'

class CollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [
        ManifestInline,
    ]
    resource_class = CollectionResource
    pass     
    list_display = ('id', 'pid', 'metadata', 'summary', 'label')
    
admin.site.register(Collection, CollectionAdmin)