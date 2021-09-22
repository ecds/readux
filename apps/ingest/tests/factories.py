from os.path import join
import boto3
from moto import mock_s3
from factory.django import DjangoModelFactory, FileField
from factory import Faker, SubFactory
from django.conf import settings
from apps.iiif.manifests.tests.factories import ImageServerFactory
from apps.ingest.models import Bulk, Local, Remote

class LocalFactory(DjangoModelFactory):
    class Meta:
        model = Local

    bundle = FileField(filename='bundle.zip', filepath=join(settings.APPS_DIR, 'ingest/fixtures/bundle.zip'))
    image_server = SubFactory(ImageServerFactory)
    manifest = None

class RemoteFactory(DjangoModelFactory):
    class Meta:
        model = Remote

    manifest = None
    remote_url = Faker('url')

class BulkFactory(DjangoModelFactory):
    class Meta:
        model = Bulk

    volume_files = FileField(filename='bundle.zip', filepath=join(settings.APPS_DIR, 'ingest/fixtures/bundle.zip'))
    image_server = SubFactory(ImageServerFactory)