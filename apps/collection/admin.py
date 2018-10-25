from django.contrib import admin

from .models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'depth',
        'label',
        'type',
        'updated_at',
        'created_at',
    ]

    search_fields = [
        'id',
        'depth',
        'context',
        'identification',
        'type',
        'label',
        'description',
        'attribution',
    ]

    list_per_page = 25
    readonly_fields = ['children']