from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group

from readux.annotations.models import Annotation, AnnotationGroup


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
    # readonly_fields = ('text', 'quote', 'extra_data', 'uri_link')
    readonly_fields = ('text', 'quote', 'uri_link')


# custom model form to allow users to be edited on the group
# edit form using the admin horizontal widget; based on
# http://stackoverflow.com/questions/9879687/adding-a-manytomanywidget-to-the-reverse-of-a-manytomanyfield-in-the-django-admi

class AnnotationGroupForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        User.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Users', False),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(AnnotationGroupForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            initial_users = self.instance.user_set.values_list('pk', flat=True)
            self.initial['users'] = initial_users

    def save(self, *args, **kwargs):
        kwargs['commit'] = True
        return super(AnnotationGroupForm, self).save(*args, **kwargs)

    def save_m2m(self):
        self.instance.user_set.clear()
        self.instance.user_set.add(*self.cleaned_data['users'])


class AnnotationGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_members', 'created', 'updated')
    date_hierarchy = 'created'
    exclude = ('permissions',)
    form = AnnotationGroupForm

#  customize default group display to indicate annotation groups #

# patch in a boolean property field to indicate annotation groups
def is_annotationgroup(obj):
    return hasattr(obj, 'annotationgroup')
is_annotationgroup.boolean = True
is_annotationgroup.short_description = 'Annotation group'

Group.is_annotationgroup = is_annotationgroup


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_annotationgroup')


admin.site.register(Annotation, AnnotationAdmin)
admin.site.register(AnnotationGroup, AnnotationGroupAdmin)


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)