"""Forms for Readux search"""

from django import forms

class ManifestSearchForm(forms.Form):
    """Django form for searching Manifests via Elasticsearch"""
    q = forms.CharField(
        label="Search volumes by keyword",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search volumes by keyword",
                "aria-label": "Search volumes by keyword",
                "type": "search",
                "class": "uk-input",
            },
        ),
    )
