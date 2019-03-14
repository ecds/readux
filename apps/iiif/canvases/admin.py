from django.contrib import admin

from apps.iiif.canvases.models import Canvas, IServer

class CanvasAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'pid', 'height', 'width', 'position', 'manifest', 'label')
    
class IServerAdmin(admin.ModelAdmin):
    list_display = ('IIIF_IMAGE_SERVER_BASE',)
    
admin.site.register(Canvas, CanvasAdmin)
admin.site.register(IServer, IServerAdmin)