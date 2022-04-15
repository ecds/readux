"""Validators for Manifests models"""
from django.forms import ValidationError
from edtf import parse_edtf
from pyparsing import ParseException


def validate_edtf(value):
    """Validator for EDTF field"""
    try:
        parse_edtf(value)
    except ParseException as edtf_parsing_error:
        raise ValidationError(
            'Invalid EDTF date: "%(value)s". Please conform to the EDTF specification.',
            code='invalid_edtf',
            params={'value': value},
        ) from edtf_parsing_error
