from django.contrib import admin

from .models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'label',
        'updated_at',
        'created_at',
    ]

    search_fields = [
        'id',
        'identification',
        'label',
        'summary',
        'attribution',
    ]

    list_per_page = 25
    # readonly_fields = ['children']