"""
Factory to create collestions for testing.
"""
import random
from factory.django import DjangoModelFactory, ImageField
from factory import Faker
from time import time
from apps.utils.noid import encode_noid
from ..models import Collection

class CollectionFactory(DjangoModelFactory):
    """
    Factory for mocking :class:`apps.iiif.kollections.models.Collection` objects.
    """
    pid = encode_noid(int(time()))
    label = Faker("name")
    original = ImageField(
        width=1024,
        height=728,
        filename='example.jpg'
    )

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Collection
