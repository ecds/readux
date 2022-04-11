"""Forms for Readux search"""

from django import forms
from django.template.defaultfilters import truncatechars

class FacetedMultipleChoiceField(forms.MultipleChoiceField):
    """MultipleChoiceField populated by Elasticsearch facets"""
    # adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/

    def populate_from_buckets(self, buckets):
        """Populate the field choices from the buckets returned by Elasticsearch."""
        self.choices = (
            (
                bucket["key"],
                f'{truncatechars(bucket["key"], 42)} ({bucket["doc_count"]})',
            )
            for bucket in sorted(buckets, key=lambda b: -b["doc_count"]) # sort choices by count
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
    collection = FacetedMultipleChoiceField(
        label="Collection",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "aria-label": "Filter volumes by collection",
                "class": "uk-input",
            },
        ),
    )
    sort = forms.ChoiceField(
        label="Sort",
        required=False,
        choices=(  # The first value of these tuples must match an ES index (or meta, like _score)
            ("-created_at", "Date added (newest first)"),
            ("created_at", "Date added (oldest first)"),
            ("-date_sort_descending", "Date published (newest first)"),
            ("date_sort_ascending", "Date published (oldest first)"),
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
