"""Tests for custom form components for search"""

import random
import string
from unittest.mock import Mock
from apps.readux.forms import FacetedMultipleChoiceField, ManifestSearchForm


class TestFacetedMultipleChoiceField:
    """Tests for multiple choice field for Elasticsearch facets"""

    def test_valid_value(self):
        """Should always return True"""
        facetfield = FacetedMultipleChoiceField()
        assert facetfield.valid_value("junk_string")

    def test_populate_from_buckets(self):
        """Should return choices based on passed buckets"""
        facetfield = FacetedMultipleChoiceField()
        fake_buckets = [{"key": "fake1", "doc_count": 0}, {"key": "fake2", "doc_count": 12}]
        facetfield.populate_from_buckets(buckets=fake_buckets)
        assert ("fake1", "fake1 (0)") in facetfield.choices
        assert ("fake2", "fake2 (12)") in facetfield.choices

        # should truncate keys >= 64 characters for label
        random_100_chars = ''.join(random.choices(string.ascii_letters, k=100))
        fake_buckets = [{"key": random_100_chars, "doc_count": 120}]
        facetfield.populate_from_buckets(buckets=fake_buckets)
        assert (random_100_chars, f"{random_100_chars} (120)") not in facetfield.choices
        truncated = f"{random_100_chars[0:63]}…"
        assert (random_100_chars, f"{truncated} (120)") in facetfield.choices


class TestManifestSearchForm:
    """Tests for search form custom methods"""

    def test_set_facets(self):
        """Should call populate method on form fields based on facets retrieved from view"""
        form = ManifestSearchForm()
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
