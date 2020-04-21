"""Django Admin module for Readux."""
from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, JSONWidget
from apps.readux.models import UserAnnotation
from apps.iiif.canvases.models import Canvas

class UserAnnotationResource(resources.ModelResource):
    """Django Admin Model Resource for UserAnnotation:"""
    canvas_link = fields.Field(
        column_name='canvas',
        attribute='canvas',
        widget=ForeignKeyWidget(Canvas, 'pid'))
    oa_annotation = fields.Field(
        attribute='oa_annotation',
        column_name='oa_annotation',
        widget=JSONWidget)
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = UserAnnotation
        fields = (
            'id', 'x', 'y', 'w', 'h', 'order', 'content',
            'resource_type', 'motivation', 'format',
            'canvas_link', 'language', 'oa_annotation'
        )


class UserAnnotationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Django Admin configuration for UserAnnotation"""
    resource_class = UserAnnotationResource
    list_display = ('id', 'canvas', 'order', 'content', 'x', 'y', 'w', 'h')
    search_fields = ('content', 'oa_annotation')

admin.site.register(UserAnnotation, UserAnnotationAdmin)
