from django.contrib import admin
from django import forms
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.models import Manifest, Note

#class ManifestModelChoiceField(forms.ModelChoiceField):
#    def label_from_instance(self, obj):
#        """
#        This method is used to convert objects into strings; it's used to
#        generate the labels for the choices presented by this object. Subclasses
#        can override this method to customize the display of the choices.
#        """
#        # Then return what you'd like to display
#       return "%s " % (self.manifest.label)
        
#class MyForm(forms.ModelForm):
#    collection = ManifestModelChoiceField(
#        queryset=Manifest.objects.all()
#    )
#
#    class Meta:
#        model = Manifest
#        fields = ['label',]
#def formfield_for_manytomany(self, db_field, request, **kwargs):
#    if db_field.name == 'Manifest_collections':
#        return ManifestModelChoiceField(queryset=Manifest.collections.through.objects.all())
#    return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
class CollectionResource(resources.ModelResource):
    class Meta:
        model = Collection
        fields = ('id', 'label','summary', 'pid', 'attribution', 'metadata', 'original', 'collection_image_title', 'collection_image_creator', 'collection_image_summary')

class ManifestInline(admin.TabularInline):
#    form = MyForm
    model = Manifest.collections.through
    fields = ('manifest', 'manifest_pid')
#    filter_horizontal = ('manifest',)
    autocomplete_fields = ('manifest',)
    readonly_fields = ('manifest_pid',)
    verbose_name_plural = 'Manifests in this Collection'

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