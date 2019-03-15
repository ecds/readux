from django.contrib import admin

from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from apps.iiif.annotations.models import Annotation
from apps.iiif.canvases.models import Canvas

class AnnotationResource(resources.ModelResource):
    canvas_link = fields.Field(
        column_name='canvas',
        attribute='canvas',
        widget=ForeignKeyWidget(Canvas, 'pid'))
    class Meta:
        model = Annotation
        fields = ('id', 'x','y','w','h','order','content','resource_type','motivation','format','canvas_link')


class AnnotationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = AnnotationResource
    pass     
    list_display = ('id', 'canvas', 'order', 'content', 'x', 'y', 'w', 'h')
    
admin.site.register(Annotation, AnnotationAdmin)