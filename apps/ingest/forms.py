from django import forms
from django.forms import ClearableFileInput
from .models import Bulk


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class BulkVolumeUploadForm(forms.ModelForm):
    class Meta:
        model = Bulk
        fields = ["image_server", "volume_files", "collections"]
        widgets = {
            "volume_files": MultipleFileInput,
        }
