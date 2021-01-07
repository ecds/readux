"""Django admin module for :class:`apps.iiif.annotations`"""
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, JSONWidget
from .models import Annotation, AnnotationGroup
from ..canvases.models import Canvas
from django.contrib.auth import get_user_model

User = get_user_model()

class AnnotationResource(resources.ModelResource):
    """Annotation resource"""
    canvas_link = fields.Field(
        column_name='canvas',
        attribute='canvas',
        widget=ForeignKeyWidget(Canvas, 'pid'))
    oa_annotation = fields.Field(
        attribute='oa_annotation',
        column_name='oa_annotation',
        widget=JSONWidget)
    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Annotation
        fields = (
            'id', 'x', 'y', 'w', 'h' , 'order',
            'content', 'resource_type', 'motivation',
            'format', 'canvas_link', 'language', 'oa_annotation'
        )

class AnnotationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Annotation admin"""
    resource_class = AnnotationResource
    list_display = ('id', 'canvas', 'order', 'content', 'x', 'y', 'w', 'h')
    search_fields = ('content', 'oa_annotation', 'canvas__pid')

# Code from 1.8
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


admin.site.register(Annotation, AnnotationAdmin)
admin.site.register(AnnotationGroup, AnnotationGroupAdmin)


admin.site.unregister(Group)
#admin.site.register(Group, GroupAdmin)
