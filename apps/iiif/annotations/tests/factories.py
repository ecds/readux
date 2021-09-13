"""Factory to create Annotations for Tests"""
from random import randrange
from factory.django import DjangoModelFactory
from factory import Faker
from apps.users.tests.factories import UserFactory
from ..models import Annotation

class AnnotationFactory(DjangoModelFactory):
    """Creates OCR like Annotation object for testing."""
    x = randrange(100, 1000)
    y = randrange(100, 1000)
    h = randrange(10, 100)
    w = randrange(10, 100)
    order = randrange(1, 100)
    resource_type = 'cnt:ContentAsText'
    content = Faker('text')
    motivation = "sc:painting"
    format = "text/plain"
    oa_annotation = {
        "annotatedBy": {
            "name": "ocr"
        }
    }

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Annotation
