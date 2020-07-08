"""Factory to create Manifests for Tests"""
from random import randrange
from factory import DjangoModelFactory, Faker, RelatedFactory
from factory.django import ImageField
from ..models import Manifest
from ...canvases.tests.factories import CanvasFactory

class ManifestFactory(DjangoModelFactory):
    """Creates a Manifest object for testing."""
    pid = str(randrange(2000, 5000))
    label = Faker("name")
    canvase = RelatedFactory(CanvasFactory, 'manifest')
    logo = ImageField(from_path='apps/iiif/canvases/tests/ecds.png')

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest
