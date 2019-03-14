from django.contrib import admin

from apps.iiif.manifests.models import Manifest


class ManifestAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'pid', 'label', 'author', 'published_date', 'published_city', 'publisher', 'collection')
    
admin.site.register(Manifest, ManifestAdmin)