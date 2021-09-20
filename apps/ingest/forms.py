from django import forms
from django.forms import ClearableFileInput
from .models import Bulk

class BulkVolumeUploadForm(forms.ModelForm):
    class Meta:
        model = Bulk
        fields = ['image_server', 'volume_files']
        widgets = {
            'volume_files': ClearableFileInput(attrs={'multiple': True}),
        }
