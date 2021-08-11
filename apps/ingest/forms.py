from django import forms

class FileFieldForm(forms.ModelForm):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

# class BulkAdminForm