""" Tests for ingest.services """
import os
import boto3
from moto import mock_s3
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.tests.factories import CanvasFactory, IServerFactory
from apps.iiif.manifests.tests.factories import ManifestFactory
from ..models import Local
from ..services import UploadBundle

class ServicesTest(TestCase):
    """ Tests for ingest.services """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(str(settings.APPS_DIR), 'ingest/fixtures/')

    @mock_s3
    def test_s3_upload_from_local(self):
        """ It should upload the images using a fake S3 service from moto. """
        local = Local(
            image_server = IServerFactory(
                IIIF_IMAGE_SERVER_BASE='http://images.readux.ecds.emory',
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

        upload_service = UploadBundle(
            canvas=CanvasFactory(
                IIIF_IMAGE_SERVER_BASE=local.image_server,
                ocr_file_path=os.path.join(local.ocr_directory, '00000005.tsv'),
                manifest=ManifestFactory()
            ),
            file_path=os.path.join(local.image_directory, '00000005.jpg')
        )

        upload_service.upload_bundle()
