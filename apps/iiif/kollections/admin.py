from django.contrib import admin
from django import forms
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.models import Manifest, Note

#class ManifestModelChoiceField(forms.ModelChoiceField()):
#    def label_from_instance(self, obj):
#        """
#        This method is used to convert objects into strings; it's used to
#        generate the labels for the choices presented by this object. Subclasses
#        can override this method to customize the display of the choices.
#        """
#        # Then return what you'd like to display
        return "Manifest{0} - Manifest.label{1}".format(obj.pk, obj.label)
        
#class MyForm(forms.ModelForm):
#    manifest = ManifestModelChoiceField(
#        queryset=Manifest.objects.select_related('manifests').all()
#    )
#
#    class Meta:
#        model = Manifest
        
class CollectionResource(resources.ModelResource):
    class Meta:
        model = Collection
        fields = ('id', 'label','summary', 'pid','metadata', 'upload')

class ManifestInline(admin.TabularInline):
#    form = MyForm
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