"""
Factory for created canvas objects for testing.
"""
import random
from factory import DjangoModelFactory, Faker, SubFactory
from ..models import Canvas, IServer

class IServerFactory(DjangoModelFactory):
    IIIF_IMAGE_SERVER_BASE = 'http://images.ecds.emory.edu'
    storage_service = 'sftp'
    storage_path = 'readux'

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = IServer

class CanvasFactory(DjangoModelFactory):
    pid = str(random.randrange(2000, 5000) + random.randrange(200, 500))
    label = Faker("name")
    height = random.randrange(200, 500)
    width = random.randrange(200, 500)
    position = random.randrange(5)
    IIIF_IMAGE_SERVER_BASE = SubFactory(IServerFactory)
    manifest = None
    ocr_file_path = None

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Canvas
