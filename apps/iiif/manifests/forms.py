"""Django Forms for export."""
import csv
from io import StringIO
import logging
from django import forms
from django.contrib.admin import site as admin_site, widgets
from django.core.validators import FileExtensionValidator

from apps.iiif.manifests.models import Manifest
from apps.iiif.canvases.models import Canvas
from apps.ingest.services import normalize_header

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
            'image_server', 'start_canvas', 'attribution', 'logo', 'logo_url', 'license', 'scanned_by', 'identifier', 'identifier_uri'
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

class ManifestCSVImportForm(forms.Form):
    """Form to import a CSV and update the metadata for multiple manifests"""

    csv_file = forms.FileField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        label="CSV File",
        help_text="""
            <p>Provide a CSV with a <strong>pid</strong> column, whose value in each row must match
            the PID of an existing volume. Additional columns will be used to update the volume's
            metadata.</p>
            <p>Columns matching <strong>Manifest</strong> model field names will update those
            fields directly, and any additional columns will be used to populate the volume's
            <strong>metadata</strong> JSON field.</p>
        """,
    )

    def clean(self):
        # check csv has pid column
        super().clean()
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            reader = csv.DictReader(
                normalize_header(
                    StringIO(csv_file.read().decode('utf-8'))
                ),
            )
            if 'pid' not in reader.fieldnames:
                self.add_error(
                    'metadata_spreadsheet',
                    forms.ValidationError(
                        """Spreadsheet must have pid column. Check to ensure there
                        are no stray characters in the header row."""
                    ),
                )
            # return back to start of file so we can read again
            csv_file.seek(0, 0)
        return self.cleaned_data
