from os.path import join
import boto3
from moto import mock_s3
from factory.django import DjangoModelFactory, FileField
from factory import Faker, SubFactory
from django.conf import settings
from apps.iiif.manifests.tests.factories import ImageServerFactory
from apps.ingest.models import Local

@mock_s3
class LocalFactory(DjangoModelFactory):
    def __init__(self, **kwargs):
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=self.image_server.storage_path)
        conn.create_bucket(Bucket='readux-ingest')

    class Meta:
        model = Local

    bundle = FileField(filename='bundle.zip', filepath=join(settings.APPS_DIR, 'ingest/fixtures/bundle.zip'))
    image_server = SubFactory(ImageServerFactory)
    manifest = None
