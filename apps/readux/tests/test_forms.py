"""Tests for custom form components for search"""

import random
import string
from unittest.mock import Mock, call, patch
from apps.readux import forms


class TestFacetedMultipleChoiceField:
    """Tests for multiple choice field for Elasticsearch facets"""

    def test_valid_value(self):
        """Should always return True"""
        facetfield = forms.FacetedMultipleChoiceField()
        assert facetfield.valid_value("junk_string")

    def test_populate_from_buckets(self):
        """Should return choices based on passed buckets"""
        facetfield = forms.FacetedMultipleChoiceField()
        fake_buckets = [{"key": "fake1", "doc_count": 0}, {"key": "fake2", "doc_count": 12}]
        facetfield.populate_from_buckets(buckets=fake_buckets)
        assert ("fake1", "fake1 (0)") in facetfield.choices
        assert ("fake2", "fake2 (12)") in facetfield.choices

        # should truncate keys >= 42 characters for label
        random_100_chars = ''.join(random.choices(string.ascii_letters, k=100))
        fake_buckets = [{"key": random_100_chars, "doc_count": 120}]
        facetfield.populate_from_buckets(buckets=fake_buckets)
        assert (random_100_chars, f"{random_100_chars} (120)") not in facetfield.choices
        truncated = f"{random_100_chars[0:41]}…"
        assert (random_100_chars, f"{truncated} (120)") in facetfield.choices


class TestManifestSearchForm:
    """Tests for search form custom methods"""

    def test_set_facets(self):
        """Should call populate method on form fields based on facets retrieved from view"""
        form = forms.ManifestSearchForm()
        example_field = Mock()
        example_field.populate_from_buckets = Mock()
        fake_buckets = [{"key": "fake1", "doc_count": 0}, {"key": "fake2", "doc_count": 12}]
        form.fields = {
            "example_field": example_field,
        }
        facets = {
            "example_field": fake_buckets
        }
        form.set_facets(facets=facets)
        example_field.populate_from_buckets.assert_called_with(fake_buckets)

    @patch("apps.readux.forms.MinMaxDateField.set_initial")
    def test_set_date(self, mock_set_initial):
        """Should call set_initial on start_date and end_date form fields with formatted dates"""
        min_date = "2022-01-01T00:00:00.000Z"
        max_date = "2022-12-31T00:00:00.000Z"
        form = forms.ManifestSearchForm()
        form.set_date(min_date, max_date)
        mock_set_initial.assert_has_calls([call("2022-01-01"), call("2022-12-31")], any_order=True)


class TestMinMaxDateField:
    """Tests for DateField populated by elasticsearch min or max date"""

    def test_set_initial(self):
        """Should set initial and attribute on widget"""
        date_field = forms.MinMaxDateField(widget=forms.MinMaxDateInput())
        date_field.set_initial("2022-01-01")
        assert date_field.initial == "2022-01-01"
        assert date_field.widget.date_initial == "2022-01-01"


class TestMinMaxDateInput:
    """Tests for widget populated by an initial date"""

    def test_get_context(self):
        """Should set data-date-initial attribute"""
        date_widget = forms.MinMaxDateInput()
        date_widget.date_initial = "2022-01-01"
        assert date_widget.get_context(
            name="start_date", value="", attrs={}
        )["widget"]["attrs"]["data-date-initial"] == "2022-01-01"
