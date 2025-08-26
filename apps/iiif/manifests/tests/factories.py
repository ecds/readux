"""Factory to create Manifests for Tests"""

from datetime import datetime
from factory.django import DjangoModelFactory, ImageField
from factory import Faker, RelatedFactory, SubFactory
from apps.utils.noid import encode_noid
from ..models import Manifest, ImageServer, Language
from ...canvases.tests.factories import CanvasFactory


class LanguageFactory(DjangoModelFactory):
    """Factory for language objects."""

    class Meta:
        model = Language


class ImageServerFactory(DjangoModelFactory):
    server_base = "http://images.ecds.emory.edu"
    storage_service = "sftp"
    storage_path = "readux"

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = ImageServer


class ManifestFactory(DjangoModelFactory):
    """Creates a Manifest object for testing."""

    pid = encode_noid()
    label = Faker("name")
    author = Faker("name")
    publisher = Faker("company")
    published_city = Faker("city")
    published_date = Faker("date")
    canvases = RelatedFactory(CanvasFactory, "manifest")
    logo = ImageField(from_path="apps/iiif/canvases/tests/ecds.png")
    image_server = SubFactory(ImageServerFactory)
    summary = Faker("sentence")

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest


class EmptyManifestFactory(DjangoModelFactory):
    """Creates a Manifest object for testing."""

    pid = encode_noid()
    label = Faker("name")
    logo = ImageField(from_path="apps/iiif/canvases/tests/ecds.png")
    image_server = SubFactory(ImageServerFactory)

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Manifest
