"""
Factory for created canvas objects for testing.
"""
from factory.django import DjangoModelFactory
from ..models import Style

class StyleFactory(DjangoModelFactory):
    """
    Generate :class:`apps.CustomStyle.models.Style` object
    for testingtype DjangoModelFactory: [type]
    """
    primary_color = '#950953'
    active = False

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Style
