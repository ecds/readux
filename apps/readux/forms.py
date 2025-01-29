"""Forms for Readux search"""

from dateutil import parser
from django import forms
from django.forms import widgets
from django.conf import settings
from django.template.defaultfilters import truncatechars


class MinMaxDateInput(forms.DateInput):
    """Widget extending DateInput to include an initial date in its attrs"""

    date_initial = ""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["data-date-initial"] = self.date_initial
        return context


class MinMaxDateField(forms.DateField):
    """DateField populated by Elasticsearch min or max date"""

    def set_initial(self, date):
        """Set the initial date to the passed date"""
        self.initial = date
        self.widget.date_initial = date


class FacetedMultipleChoiceField(forms.MultipleChoiceField):
    """MultipleChoiceField populated by Elasticsearch facets"""

    # adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/

    def populate_from_buckets(self, buckets):
        """Populate the field choices from the buckets returned by Elasticsearch."""
        self.choices = (
            (
                bucket["key"],
                f'{truncatechars(bucket["key"], 42) if len(bucket["key"]) > 0 else "None"} ({bucket["doc_count"]})',
            )
            for bucket in sorted(
                buckets, key=lambda b: -b["doc_count"]
            )  # sort choices by count
        )

    def valid_value(self, value):
        """failsafe for chosen but unloaded facet"""
        return True


class ManifestSearchForm(forms.Form):
    """Django form for searching Manifests via Elasticsearch"""

    q = forms.CharField(
        label="Search for individual whole keywords. Multiple words will be searched as 'or' (e.g. Rome London = Rome or London).",
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
    scope = forms.ChoiceField(
        label="Limit search to",
        required=False,
        initial="all",
        choices=(
            ("all", "All"),
            ("metadata", "Metadata only"),
            ("text", "Textual contents only"),
        ),
        widget=forms.Select(
            attrs={
                "class": "uk-select",
            },
        ),
    )
    language = FacetedMultipleChoiceField(
        label="Language",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "aria-label": "Filter volumes by language",
                # "class": "uk-input",
            },
        ),
    )
    author = FacetedMultipleChoiceField(
        label="Author",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "aria-label": "Filter volumes by author",
                # "class": "uk-input",
            },
        ),
    )
    collection = FacetedMultipleChoiceField(
        label="Collection",
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "aria-label": "Filter volumes by collection",
                # "class": "uk-input",
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
            ("label_alphabetical", "Title (A-Z)"),
            ("-label_alphabetical", "Title (Z-A)"),
            ("_score", "Relevance"),
        ),
        widget=forms.Select(
            attrs={
                "class": "uk-select",
            },
        ),
    )
    start_date = MinMaxDateField(
        label="Start date",
        required=False,
        widget=MinMaxDateInput(
            attrs={
                "type": "date",
            },
            format="%Y-%m-%d",
        ),
    )
    end_date = MinMaxDateField(
        label="End date",
        required=False,
        widget=MinMaxDateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d",
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # pull additional facets from Elasticsearch
        if (
            settings
            and hasattr(settings, "CUSTOM_METADATA")
            and isinstance(settings.CUSTOM_METADATA, dict)
        ):
            # should be a dict like {meta_key: {"multi": bool, "separator": str, "faceted": bool}}
            for key in [
                k
                for k in settings.CUSTOM_METADATA.keys()
                if settings.CUSTOM_METADATA[k].get("faceted", False)
            ]:
                self.fields[
                    # use django-friendly form field names
                    key.casefold().replace(" ", "_")
                ] = FacetedMultipleChoiceField(
                    label=key,
                    required=False,
                    widget=forms.SelectMultiple(
                        attrs={
                            "aria-label": f"Filter volumes by {key}",
                            "class": "uk-input",
                        },
                    ),
                )

    def set_facets(self, facets):
        """Use facets from Elasticsearch to populate form fields"""
        for name, buckets in facets.items():
            if name in self.fields:
                # Assumes that name passed in the view's facets list matches form field name
                self.fields[name].populate_from_buckets(buckets)
            elif name.casefold().replace(" ", "_") in self.fields:
                self.fields[name.casefold().replace(" ", "_")].populate_from_buckets(
                    buckets
                )

    def set_date(self, min_date, max_date):
        """Use min and max aggregations from Elasticsearch to populate date range fields"""
        min_date_object = parser.isoparse(min_date)
        self.fields["start_date"].set_initial(min_date_object.strftime("%Y-%m-%d"))
        max_date_object = parser.isoparse(max_date)
        self.fields["end_date"].set_initial(max_date_object.strftime("%Y-%m-%d"))


class CustomDropdownSelect(widgets.ChoiceWidget):
    """A custom select widget that uses uk-navbar-dropdown to present its options,
    and submits the form on any change"""

    input_type = "radio"
    template_name = "widgets/custom_dropdown_select.html"
    option_template_name = "django/forms/widgets/radio_option.html"

    def get_context(self, name, value, attrs):
        """Add the label for the selected option to template context"""
        context = super().get_context(name, value, attrs)
        context["selected_value_label"] = dict(self.choices).get(value, None)
        return context


class AllVolumesForm(forms.Form):
    """Simple form for sorting Manifests"""

    SORT_CHOICES = [
        ("title", "Title"),
        ("author", "Author"),
        ("date", "Publication Year"),
        ("added", "Date Added"),
    ]
    ORDER_CHOICES = [
        ("asc", "Ascending"),
        ("desc", "Descending"),
    ]
    sort = forms.ChoiceField(
        label="Sort by",
        choices=SORT_CHOICES,
        required=False,
        widget=CustomDropdownSelect,
    )
    order = forms.ChoiceField(
        label="Order",
        choices=ORDER_CHOICES,
        required=False,
        widget=CustomDropdownSelect,
    )


class AllCollectionsForm(forms.Form):
    """Simple form for sorting Collections"""

    SORT_CHOICES = [
        ("title", "Title"),
        ("added", "Date Added"),
        ("volumes", "Number of Volumes"),
    ]
    ORDER_CHOICES = [
        ("asc", "Ascending"),
        ("desc", "Descending"),
    ]
    sort = forms.ChoiceField(
        label="Sort by",
        choices=SORT_CHOICES,
        required=False,
        widget=CustomDropdownSelect,
    )
    order = forms.ChoiceField(
        label="Order",
        choices=ORDER_CHOICES,
        required=False,
        widget=CustomDropdownSelect,
    )
