from django.contrib import admin

from readux.collection.models import CollectionImage


class CollectionImageAdmin(admin.ModelAdmin):
    list_display = ('collection_label', 'cover', 'cover_thumbnail',
                    'banner', 'banner_thumbnail')

admin.site.register(CollectionImage, CollectionImageAdmin)
