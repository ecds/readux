import random
from factory import DjangoModelFactory, Faker, RelatedFactory
from ..models import Manifest
from ...canvases.tests.factories import CanvasFactory

class ManifestFactory(DjangoModelFactory):
    pid = str(random.randrange(2000, 5000))
    label = Faker("name")
    canvase = RelatedFactory(CanvasFactory, 'manifest')

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest
