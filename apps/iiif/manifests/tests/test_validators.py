"""Tests for validation functions"""
from django.forms import ValidationError
from django.test import TestCase
from apps.iiif.manifests import validators


class TestValidateEDTF(TestCase):
    """Tests for EDTF validation"""
    def test_validate_edtf(self):
        """Should raise ValidationError on invalid EDTF"""
        with self.assertRaises(ValidationError):
            validators.validate_edtf("bad edtf")

        # Should not accept natural language uncertainty
        with self.assertRaises(ValidationError):
            validators.validate_edtf("circa 1900")

        # Should accept EDTF Level 0, 1, 2
        try:
            validators.validate_edtf("1900-01-01/1900-12-31")  # level 0 interval
        except ValidationError:
            self.fail("validate_edtf raised ValidationError on level 0")
        try:
            validators.validate_edtf("1900~")  # level 1 approximate date
        except ValidationError:
            self.fail("validate_edtf raised ValidationError on level 1")
        try:
            validators.validate_edtf("190x")  # level 2 masked precision
        except ValidationError:
            self.fail("validate_edtf raised ValidationError on level 2")
