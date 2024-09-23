"""
Django admin module for kollections
"""
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from apps.iiif.manifests.admin import SummernoteMixin
from .models import Collection
from ..manifests.models import Manifest

class CollectionResource(resources.ModelResource):
    """Django admin collection resource"""
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Collection
        fields = (
            'id', 'label', 'summary', 'pid', 'attribution',
            'metadata', 'original', 'collection_image_title',
            'collection_image_creator', 'collection_image_summary'
        )

class ManifestInline(admin.TabularInline):
    """Django admin inline configuration for a manifest."""
    model = Manifest.collections.through
    fields = ('manifest', 'manifest_pid')
    autocomplete_fields = ('manifest',)
    readonly_fields = ('manifest_pid',)
    verbose_name_plural = 'Manifests in this Collection'

    # TODO: Test this
    def manifest_pid(self, instance):
        """Convenience method to get manifest pid.

        :return: [description]
        :rtype: str
        """
        return instance.manifest.pid

    manifest_pid.short_description = 'Manifest Local ID'

class CollectionAdmin(ImportExportModelAdmin, SummernoteMixin, admin.ModelAdmin):
    """Django admin configuration for a collection."""
    inlines = [
        ManifestInline,
    ]
    resource_class = CollectionResource
    list_display = ('id', 'pid', 'metadata', 'summary', 'label')
    search_fields = ('label', 'summary', 'pid')
    summernote_fields = ('summary', 'summary_en',)

admin.site.register(Collection, CollectionAdmin)
