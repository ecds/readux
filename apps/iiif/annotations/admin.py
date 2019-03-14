from django.contrib import admin

from apps.iiif.annotations.models import Annotation

class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'content', 'x', 'y', 'w', 'h')
    
admin.site.register(Annotation, AnnotationAdmin)