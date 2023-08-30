"""Factory to create Manifests for Tests"""
from random import randrange
from factory.django import DjangoModelFactory, ImageField
from factory import Faker, RelatedFactory, SubFactory
from time import time
from apps.utils.noid import encode_noid
from ..models import Manifest, ImageServer
from ...canvases.tests.factories import CanvasFactory

class ImageServerFactory(DjangoModelFactory):
    server_base = 'http://images.ecds.emory.edu'
    storage_service = 'sftp'
    storage_path = 'readux'

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = ImageServer

class ManifestFactory(DjangoModelFactory):
    """Creates a Manifest object for testing."""
    pid = encode_noid()
    label = Faker("name")
    canvases = RelatedFactory(CanvasFactory, 'manifest')
    logo = ImageField(from_path='apps/iiif/canvases/tests/ecds.png')
    image_server = SubFactory(ImageServerFactory)
    summary = Faker('sentence')

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest

class EmptyManifestFactory(DjangoModelFactory):
    """Creates a Manifest object for testing."""
    pid = encode_noid()
    label = Faker("name")
    logo = ImageField(from_path='apps/iiif/canvases/tests/ecds.png')
    image_server = SubFactory(ImageServerFactory)

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest