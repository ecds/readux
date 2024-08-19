"""
Factory for created canvas objects for testing.
"""
import random
from factory.django import DjangoModelFactory
from factory import Faker
from apps.utils.noid import encode_noid
from ..models import Canvas

class CanvasFactory(DjangoModelFactory):
    label = Faker("name")
    height = random.randrange(200, 500)
    width = random.randrange(200, 500)
    position = random.randrange(5)
    manifest = None
    ocr_file_path = None
    default_ocr = 'word'

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Canvas

class CanvasNoDimensionsFactory(CanvasFactory):
    height = 0
    width = 0
