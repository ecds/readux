"""Factories for creating objects for testing."""
from factory import DjangoModelFactory
from ..models import Annotation

class AnnotationFactory(DjangoModelFactory):
    """Factory for creating `Annotation` objects for testing."""
    # pid = str(random.randrange(2000, 5000))
    # label = Faker("name")
    # height = random.randrange(200, 500)
    # width = random.randrange(200, 500)
    # position = random.randrange(5)
    # IIIF_IMAGE_SERVER_BASE = SubFactory(IServerFactory)

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Annotation
