from django.contrib import admin

from apps.iiif.canvases.models import Canvas

class CanvasAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'pid', 'height', 'width', 'position', 'manifest', 'label')
    
admin.site.register(Canvas, CanvasAdmin)