"""Django admin module for `apps.iiif.annotations`"""
from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, JSONWidget
from .models import Annotation
from ..canvases.models import Canvas

class AnnotationResource(resources.ModelResource):
    """Annotation resource"""
    canvas_link = fields.Field(
        column_name='canvas',
        attribute='canvas',
        widget=ForeignKeyWidget(Canvas, 'pid'))
    oa_annotation = fields.Field(
        attribute='oa_annotation',
        column_name='oa_annotation',
        widget=JSONWidget)
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Annotation
        fields = (
            'id', 'x', 'y', 'w', 'h' , 'order',
            'content', 'resource_type', 'motivation',
            'format', 'canvas_link', 'language', 'oa_annotation'
        )

class AnnotationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Annotation admin"""
    resource_class = AnnotationResource
    list_display = ('id', 'canvas', 'order', 'content', 'x', 'y', 'w', 'h')
    search_fields = ('content', 'oa_annotation', 'canvas__pid')

admin.site.register(Annotation, AnnotationAdmin)
