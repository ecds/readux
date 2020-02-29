from django.contrib import admin
from django import forms
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.models import Manifest, Note      

class CollectionResource(resources.ModelResource):
    class Meta:
        model = Collection
        fields = ('id', 'label','summary', 'pid', 'attribution', 'metadata', 'original', 'collection_image_title', 'collection_image_creator', 'collection_image_summary')

class ManifestInline(admin.TabularInline):
    model = Manifest.collections.through
    fields = ('manifest', 'manifest_pid')
    autocomplete_fields = ('manifest',)
    readonly_fields = ('manifest_pid',)
    verbose_name_plural = 'Manifests in this Collection'

    # TODO: Test this
    def manifest_pid(self, instance):
        return instance.manifest.pid

    manifest_pid.short_description = 'Manifest Local ID'

class CollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [
        ManifestInline,
    ]
    resource_class = CollectionResource
    pass     
    list_display = ('id', 'pid', 'metadata', 'summary', 'label')
    search_fields = ('label','summary','pid')
    
admin.site.register(Collection, CollectionAdmin)