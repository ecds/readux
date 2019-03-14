from django.contrib import admin

from apps.iiif.kollections.models import Collection


class CollectionAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'pid', 'metadata', 'summary', 'label')
    
admin.site.register(Collection, CollectionAdmin)