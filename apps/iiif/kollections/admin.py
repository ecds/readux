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
#        return "%s : %s" % (self.manifest.pid, self.manifest.label)
        
#class MyForm(forms.ModelForm):
#    collection = ManifestModelChoiceField(
#        queryset=manifest_collection.manifest.objects.all()
#    )
#
#    class Meta:
#        model = manifest_collection
#        fields = ['id']
#def formfield_for_manytomany(self, db_field, request, **kwargs):
#    if db_field.name == 'Manifest_collections':
#        return ManifestModelChoiceField(queryset=Manifest.collections.through.objects.all())
#    return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
class CollectionResource(resources.ModelResource):
    class Meta:
        model = Collection
        fields = ('id', 'label','summary', 'pid','metadata', 'upload')

class ManifestInline(admin.TabularInline):
#    form = MyForm
    model = Manifest.collections.through
    filter_horizontal = ('pid',)
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