from os import path, remove, mkdir, listdir
from shutil import rmtree
from io import StringIO
import pytest
import boto3
import httpretty
from csv import DictReader
from moto import mock_s3
from zipfile import ZipFile
from getpass import getuser
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from .mock_sftp import MockSFTP
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from ..models import S3Ingest
from ..services import (clean_metadata, create_manifest, get_associated_meta,
                       get_metadata_from, lowercase_first_line)

pytestmark = pytest.mark.django_db(transaction=True) # pylint: disable = invalid-name

@mock_s3
class S3Test(TestCase):
    """ Tests for ingest.models.S3Ingest """
    @classmethod
    def setUpClass(cls):
        cls.sftp_server = MockSFTP()
        cls.fixture_path = path.join(settings.APPS_DIR, 'ingest/fixtures/')
        cls.test_bundle_path = path.join(cls.fixture_path, 'test_bundle')
        cls.test_pid = 'sqn75'
        super(S3Test, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.sftp_server.stop_server()

        if path.isdir(cls.test_bundle_path):
            rmtree(cls.test_bundle_path)

        if path.isdir('images'):
            rmtree('images')


    def setUp(self):
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket='s3-ingest')


        if path.isdir(self.test_bundle_path):
            rmtree(self.test_bundle_path)

        mkdir(self.test_bundle_path)

        with ZipFile(path.join(self.fixture_path, 'csv_meta.zip'), 'r') as bundle_ref:
            bundle_ref.extractall(self.test_bundle_path)

        s3_client = boto3.client('s3')

        for filename in listdir(path.join(self.test_bundle_path, 'images')):
            with open(path.join(self.test_bundle_path, 'images', filename), 'rb') as file:
                s3_client.upload_fileobj(
                    file,
                    Bucket='s3-ingest',
                    Key=f'{self.test_pid}/images/{filename}'
                )

        for filename in listdir(path.join(self.test_bundle_path, 'ocr')):
            with open(path.join(self.test_bundle_path, 'ocr', filename), 'rb') as file:
                s3_client.upload_fileobj(
                    file,
                    Bucket='s3-ingest',
                    Key=f'{self.test_pid}/ocr/{filename}'
                )

        if path.isdir('images'):
            rmtree('images')

        mkdir('images')

        self.image_server = ImageServerFactory(
            server_base=f'http://{self.sftp_server.host}',
            storage_service='sftp',
            storage_path='images',
            sftp_port=self.sftp_server.port,
            private_key_path=self.sftp_server.key_file,
            sftp_user=getuser(),
            path_delineator='_'
        )

    def test_ingest_from_s3(self):
        httpretty.disable()
        ingest = S3Ingest(
            image_server=self.image_server,
            s3_bucket='s3-ingest',
            metadata_spreadsheet=SimpleUploadedFile(
                name='metadata.csv',
                content=open(path.join(self.test_bundle_path, 'metadata.csv'), 'rb').read()
            )
        )

        manifest = ManifestFactory.create(
            image_server=ingest.image_server,
            pid=self.test_pid,
            canvases=None
        )

        ingest.create_canvases_for(self.test_pid)

        assert path.exists(
            path.join(
                ingest.image_server.storage_path,
                f'{self.test_pid}{ingest.image_server.path_delineator}00000005.jpg'
            )
        )

        assert path.exists(
            path.join(
                ingest.image_server.storage_path,
                f'{self.test_pid}{ingest.image_server.path_delineator}00000003.tsv'
            )
        )

        manifest.refresh_from_db()
        canvas = manifest.canvas_set.all()[4]
        canvas.refresh_from_db()
        assert canvas.annotation_set.all().count() == 72
        assert manifest.canvas_set.all().count() == 10

