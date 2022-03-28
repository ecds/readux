"""Forms for Readux search"""

from django import forms

class ManifestSearchForm(forms.Form):
    """Django form for searching Manifests via Elasticsearch"""
    query = forms.CharField(
        label="Search by word or phrase",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search by word or phrase",
                "aria-label": "Search by word or phrase",
                "type": "search",
            }
        ),
    )
