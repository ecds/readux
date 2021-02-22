""" Tests for ingest.services """
import os
import boto3
from moto import mock_s3
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
import apps.ingest.services as services
from ..models import Local

class ServicesTest(TestCase):
    """ Tests for ingest.services """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')

    @mock_s3
    def test_s3_upload_from_local(self):
        """ It should upload the images using a fake S3 service from moto. """
        local = Local(
            image_server = ImageServerFactory(
                server_base='http://images.readux.ecds.emory',
                storage_service='s3',
                storage_path='readux'
            )
        )
        local.bundle = SimpleUploadedFile(
            name='bundle.zip',
            content=open(os.path.join(self.fixture_path, 'bundle.zip'), 'rb').read()
        )

        local.save()

        # Create fake bucket for moto's mock S3 service.
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=local.image_server.storage_path)

        upload_service = services.UploadBundle(
            canvas=CanvasFactory(
                ocr_file_path=os.path.join(local.ocr_directory, '00000005.tsv'),
                manifest=ManifestFactory(image_server=local.image_server)
            ),
            file_path=os.path.join(local.image_directory, '00000005.jpg')
        )

        upload_service.upload_bundle()

    @staticmethod
    def test_cleaning_metadata():
        """ It should normalize keys and remove key/value pairs that
        do not match a Manifest field. """
        fake_metadata = {
            'pid': 'blm',
            'invalid': 'trump',
            'summary': 'idk',
            'PUBLISHER': 'ecds',
            'Published City': 'atlanta'
        }

        cleaned_metadata = services.clean_metadata(fake_metadata)

        manifest_fields = [f.name for f in Manifest._meta.get_fields()]

        for key in cleaned_metadata.keys():
            assert key in manifest_fields

        assert 'Published City' not in cleaned_metadata.keys()
        assert 'PUBLISHER' not in cleaned_metadata.keys()
        assert 'invalid' not in cleaned_metadata.keys()
        assert cleaned_metadata['published_city'] == fake_metadata['Published City']
        assert cleaned_metadata['publisher'] == fake_metadata['PUBLISHER']

    @staticmethod
    def test_extracting_image_server_with_port():
        """ If should return a URL with a specified port. """
        canvas = {'@id': 'https://readux.org:8000/iiif/readux:thgg7/canvas/readux:thgg7_1.jp2'}
        image_server_url = services.extract_image_server(canvas)
        assert image_server_url == 'https://readux.org:8000/iiif'

    @staticmethod
    def test_extracting_image_server_without_port():
        """ If should return a URL with no port. """
        canvas = {'@id': 'https://readux.org/iiif/readux:thgg7/canvas/readux:thgg7_1.jp2'}
        image_server_url = services.extract_image_server(canvas)
        assert image_server_url == 'https://readux.org/iiif'
