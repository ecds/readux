"""Forms for Readux search"""

from django import forms
from django.template.defaultfilters import truncatechars

class FacetedMultipleChoiceField(forms.MultipleChoiceField):
    """MultipleChoiceField populated by Elasticsearch facets"""

    def populate_from_buckets(self, buckets):
        """Populate the field choices from the buckets returned by Elasticsearch."""
        self.choices = (
            (
                bucket["key"],
                f'{truncatechars(bucket["key"], 64)} ({bucket["doc_count"]})',
            )
            for bucket in sorted(buckets, key=lambda b: b["key"]) # sort choices by name
        )

    def valid_value(self, value):
        """failsafe for chosen but unloaded facet"""
        return True

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
    language = FacetedMultipleChoiceField(
        label="Language",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "aria-label": "Filter volumes by language",
                "class": "uk-input",
            },
        ),
    )
    author = FacetedMultipleChoiceField(
        label="Author",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "aria-label": "Filter volumes by author",
                "class": "uk-input",
            },
        ),
    )
    sort = forms.ChoiceField(
        label="Sort",
        required=False,
        choices=(
            ("label_alphabetical", "Label (A-Z)"),
            ("-label_alphabetical", "Label (Z-A)"),
            ("_score", "Relevance"),
        ),
        widget=forms.Select(
            attrs={
                "class":"uk-select",
            },
        ),
    )

    def set_facets(self, facets):
        """Use facets from Elasticsearch to populate form fields"""
        for name, buckets in facets.items():
            if name in self.fields:
                # Assumes that name passed in the view's facets list matches form field name
                self.fields[name].populate_from_buckets(buckets)
