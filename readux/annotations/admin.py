from django.contrib import admin

from readux.annotations.models import Annotation


class AnnotationAdmin(admin.ModelAdmin):
    # uuid is kind of ugly and probably not useful for display,
    # so omitting it here
    list_display = ('user', 'text_preview', 'created', 'updated',
        'uri_link')
    date_hierarchy = 'created'
    search_fields = ['id', 'text', 'quote', 'uri', 'extra_data',
        'user__username', 'user__email']
    # NOTE: searching on uuid with dashes doesn't seem to work,
    # but searching on a portion of the uuid without dashes does
    # (possibly DB dependent?)

    # for now, make these fields read-only, so annotations can only
    # be deleted or have user modified via admin; the rest should
    # be handled via the annotator interface.
    readonly_fields = ('text', 'quote', 'extra_data', 'uri_link')


admin.site.register(Annotation, AnnotationAdmin)

