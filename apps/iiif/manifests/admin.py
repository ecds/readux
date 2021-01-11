"""Django admin module for maninfests"""
from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ManyToManyWidget
from django_summernote.admin import SummernoteModelAdmin
from .models import Manifest, Note
from .forms import ManifestAdminForm
from ..kollections.models import Collection

class ManifestResource(resources.ModelResource):
    """Django admin manifest resource."""
    collection_id = fields.Field(
        column_name='collections',
        attribute='collections',
        widget=ManyToManyWidget(Collection, field='label'))
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest
        import_id_fields = ('id',)
        fields = (
            'id', 'pid', 'label', 'summary', 'author',
            'published_city', 'published_date', 'publisher',
            'pdf', 'metadata', 'viewingdirection', 'collection_id'
        )

class ManifestAdmin(ImportExportModelAdmin, SummernoteModelAdmin, admin.ModelAdmin):
    """Django admin configuration for manifests"""
    resource_class = ManifestResource
    exclude = ('id',)
    filter_horizontal = ('collections',)
    list_display = ('id', 'pid', 'label', 'author', 'published_date', 'published_city', 'publisher')
    search_fields = ('id', 'label', 'author', 'published_date')
    summernote_fields = ('summary',)
    form = ManifestAdminForm

class NoteAdmin(admin.ModelAdmin):
    """Django admin configuration for a note."""
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Note

admin.site.register(Manifest, ManifestAdmin)
admin.site.register(Note, NoteAdmin)
