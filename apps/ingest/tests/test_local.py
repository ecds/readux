""" Tests for local ingest """
import pytest
import boto3
from moto import mock_s3
from shutil import copy
from os.path import exists, join
from tempfile import gettempdir
from uuid import UUID
from unittest import mock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from ..models import Local
from ..services import create_manifest

pytestmark = pytest.mark.django_db(transaction=True) # pylint: disable = invalid-name

@mock_s3
class LocalTest(TestCase):
    """ Tests for ingest.models.Local """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = join(settings.APPS_DIR, 'ingest/fixtures/')
        self.image_server = ImageServerFactory(
            server_base='http://images.readux.ecds.emory',
            storage_service='s3',
            storage_path='readux'
        )
        # Create fake bucket for moto's mock S3 service.
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=self.image_server.storage_path)
        conn.create_bucket(Bucket='readux-ingest')

    def mock_local(self, bundle, with_manifest=False):
        # Note, I tried to use the factory here, but could not get it to override the file for bundle.
        local = Local(
            image_server = self.image_server
        )
        local.bundle = SimpleUploadedFile(
            name=bundle,
            content=open(join(self.fixture_path, bundle), 'rb').read()
        )

        local.save()

        if with_manifest:
            local.manifest = create_manifest(local)
            local.save()

        return local


    def test_bundle_upload(self):
        """ It should upload the images using a fake S3 service from moto. """
        for bundle in ['bundle.zip', 'nested_volume.zip', 'csv_meta.zip']:
            local = self.mock_local(bundle)

            assert bundle in [f.key for f in local.tmp_bucket.objects.all()]

    def test_image_upload_to_s3(self):
        local = self.mock_local('bundle.zip', True)

        local.extract_images_s3()

        image_files = [f.key for f in local.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert f'{local.manifest.pid}/00000008.jpg' in image_files

    def test_ocr_upload_to_s3(self):
        local = self.mock_local('nested_volume.zip', True)

        local.extract_ocr_s3()

        image_files = [f.key for f in local.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert f'{local.manifest.pid}/_*ocr*_/00000008.tsv' in image_files

    def test_metadata_from_excel(self):
        """ It should create a manifest with metadat supplied in an Excel file. """
        local = self.mock_local('bundle.zip', True)

        assert 'pid' in local.metadata.keys()

        for key in local.metadata.keys():
            assert local.metadata[key] == getattr(local.manifest, key)

    def test_metadata_from_csv(self):
        """ It should create a manifest with metadata supplied in a CSV file. """
        local = self.mock_local('csv_meta.zip', True)

        assert 'pid' in local.metadata.keys()

        for key in local.metadata.keys():
            assert local.metadata[key] == getattr(local.manifest, key)

    def test_metadata_from_tsv(self):
        """ It should create a manifest with metadata supplied in a CSV file. """
        local = self.mock_local('tsv.zip', True)

        assert 'pid' in local.metadata.keys()

        for key in local.metadata.keys():
            assert local.metadata[key] == getattr(local.manifest, key)

    def test_no_metadata_file(self):
        """ It should create a Manifest even when no metadata file is supplied. """
        local = self.mock_local('no_meta_file.zip', True)

        assert UUID(local.manifest.pid).version == 4

    def test_single_image(self):
        """
        """
        local = self.mock_local('single-image.zip', True)

        local.extract_images_s3()

        image_files = [f.key for f in local.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert f'{local.manifest.pid}/0011.jpg' in image_files

    def test_removing_junk(self):
        """
        Any hidden files should not be uploaded.
        """
        local = self.mock_local('bundle_with_junk.zip', True)

        local.extract_images_s3()
        local.extract_ocr_s3()

        ingest_files = [f.key for f in local.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert 'ocr/.junk.tsv' in [f.filename for f in local.zip_ref.infolist()]
        assert 'images/.00000010.jpg' in [f.filename for f in local.zip_ref.infolist()]
        assert f'{local.manifest.pid}/00000009.jpg' in ingest_files
        assert f'{local.manifest.pid}/.00000010.jpg' not in ingest_files
        assert f'{local.manifest.pid}/_*ocr*_/00000003.tsv' in ingest_files
        assert f'{local.manifest.pid}/_*ocr*_/.junk.tsv' not in ingest_files

    def test_removing_underscores(self):
        """
        Any hidden files should be removed.
        """
        local = self.mock_local('bundle_with_underscores.zip', True)

        local.extract_images_s3()
        local.extract_ocr_s3()

        ingest_files = [f.key for f in local.bucket.objects.filter(Prefix=local.manifest.pid)]

        underscore_files = [f.filename for f in local.zip_ref.infolist() if '_' in f.filename]
        assert len(underscore_files) == 10
        assert len([f.filename for f in local.zip_ref.infolist() if '-' in f.filename]) == 0
        for underscore in [f.filename for f in local.zip_ref.infolist() if '_' in f.filename]:
            assert underscore not in ingest_files

    def test_when_metadata_in_filename(self):
        """
        Make sure it doesn't get get confused when the word "metadata" is in
        every path.
        """
        local = self.mock_local('metadata.zip', True)

        local.extract_images_s3()
        local.extract_ocr_s3()

        files_in_zip = [f.filename for f in local.zip_ref.infolist()]
        ingest_files = [f.key for f in local.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert 'metadata/images/' in files_in_zip
        assert all('metadata' in f for f in files_in_zip)
        assert any('.DS_Store' in f for f in files_in_zip)
        assert any('__MACOSX' in f for f in files_in_zip)
        assert any('~$metadata.xlsx' in f for f in files_in_zip)
        assert any('metadata/ocr/0001.tsv' in f for f in files_in_zip)
        assert local.metadata['pid'] == 't9wtf-sample'
        assert local.metadata['label'] == 't9wtf-sample'
        assert '~$metadata.xlsx' not in ingest_files
        assert f'{local.manifest.pid}/_*ocr*_/0001.tsv' in ingest_files
        assert f'{local.manifest.pid}/0001.jpg' in ingest_files
        assert len(ingest_files) == 2

    def test_when_underscore_in_pid(self):
        local = self.mock_local('no_meta_file.zip')
        local.manifest = ManifestFactory.create(
            image_server = self.image_server,
            pid='p_i_d'
        )

        local.extract_images_s3()
        local.extract_ocr_s3()

        ingest_files = [f.key for f in local.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert all('p-i-d' in f for f in ingest_files)

    def test_creating_canvases(self):
        """
        Make sure it doesn't get get confused when the word "metadata" is in
        every path.
        """
        local = self.mock_local('bundle.zip', True)
        local.create_canvases()

        pid = local.manifest.pid

        assert local.manifest.canvas_set.all().count() == 10
        assert Canvas.objects.get(pid=f'{pid}_00000001.jpg').position == 1
        assert Canvas.objects.get(pid=f'{pid}_00000002.jpg').position == 2
        assert Canvas.objects.get(pid=f'{pid}_00000003.jpg').position == 3
        assert Canvas.objects.get(pid=f'{pid}_00000004.jpg').position == 4
        assert Canvas.objects.get(pid=f'{pid}_00000005.jpg').position == 5
        assert Canvas.objects.get(pid=f'{pid}_00000006.jpg').position == 6
        assert Canvas.objects.get(pid=f'{pid}_00000007.jpg').position == 7
        assert Canvas.objects.get(pid=f'{pid}_00000008.jpg').position == 8
        assert Canvas.objects.get(pid=f'{pid}_00000009.jpg').position == 9
        assert Canvas.objects.get(pid=f'{pid}_00000010.jpg').position == 10


    def test_it_downloads_zip_when_local_bundle_path_is_not_none(self):
        local = self.mock_local('metadata.zip', True)
        local.local_bundle_path = 'swoop'
        files_in_zip = [f.filename for f in local.zip_ref.infolist()]
        assert 'metadata/images/' in files_in_zip
        assert exists(join(gettempdir(), 'metadata.zip'))
        assert local.local_bundle_path == join(gettempdir(), 'metadata.zip')

    def test_it_cleans_up(self):
        local = self.mock_local('metadata.zip', True)
        local.local_bundle_path = 'swoop'
        assert exists(join(gettempdir(), 'metadata.zip'))
        local.create_canvases()
        manifest = Manifest.objects.get(pk=local.manifest.id)
        assert manifest.canvas_set.count() == 1
        assert exists(join(gettempdir(), 'metadata.zip')) is False
        try:
            Local.objects.get(pk=local.id)
        except Local.DoesNotExist:
            pass
