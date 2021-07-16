"""
Factory for created canvas objects for testing.
"""
import random
from factory.django import DjangoModelFactory
from factory import Faker
from ..models import Canvas

class CanvasFactory(DjangoModelFactory):
    pid = str(random.randrange(2000, 5000) + random.randrange(200, 500))
    label = Faker("name")
    height = random.randrange(200, 500)
    width = random.randrange(200, 500)
    position = random.randrange(5)
    manifest = None
    ocr_file_path = None

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Canvas
