"""Django Forms for export."""
import logging
from django import forms
from django.contrib.admin import site as admin_site, widgets
from .models import Language, Manifest
from ..canvases.models import Canvas

LOGGER = logging.getLogger(__name__)

# add is_checkbox method to all form fields, to enable template logic.
# thanks to:
# http://stackoverflow.com/questions/3927018/django-how-to-check-if-field-widget-is-checkbox-in-the-template
setattr(
    forms.Field,
    'is_checkbox',
    lambda self: isinstance(self.widget, forms.CheckboxInput)
)

class ManifestAdminForm(forms.ModelForm):
    """Form for adding or changing a manifest"""
    class Meta:
        model = Manifest
        fields = (
            'id', 'pid', 'label', 'summary', 'author',
            'published_city', 'published_date_edtf', 'published_date', 'publisher', 'languages',
            'pdf', 'metadata', 'viewingdirection', 'collections',
            'image_server', 'start_canvas', 'attribution', 'logo', 'license', 'scanned_by', 'identifier', 'identifier_uri'
        )
    def __init__(self, *args, **kwargs):
        super(ManifestAdminForm, self).__init__(*args, **kwargs)
        if (
                'instance' in kwargs and
                hasattr(kwargs['instance'], 'canvas_set') and kwargs['instance'].canvas_set.exists()
        ):
            self.fields['start_canvas'].queryset = kwargs['instance'].canvas_set.all()
        else:
            self.fields['start_canvas'].queryset = Canvas.objects.none()

class ManifestsCollectionsForm(forms.ModelForm):
    """Form to add manifests to collections."""
    class Meta:
        model = Manifest
        fields=('collections',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collections'].widget = widgets.RelatedFieldWidgetWrapper(
               self.fields['collections'].widget,
               self.instance._meta.get_field('collections').remote_field,
               admin_site,
        )
