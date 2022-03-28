""" Tests for local ingest """
from os import path, remove, getlogin, getcwd
from shutil import rmtree
import pytest
import boto3
import httpretty
from moto import mock_s3
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from ..models import Local
from ..services import create_manifest
from ..storages import IngestStorage

pytestmark = pytest.mark.django_db(transaction=True) # pylint: disable = invalid-name

@mock_s3
class LocalTest(TestCase):
    """ Tests for ingest.models.Local """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = path.join(settings.APPS_DIR, 'ingest/fixtures/')
        self.image_server = ImageServerFactory(
            server_base='http://readux.s3.amazonaws.com',
            storage_service='s3',
            storage_path='readux'
        )
        # Create fake bucket for moto's mock S3 service.
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=self.image_server.storage_path)
        conn.create_bucket(Bucket='readux-ingest')

    def mock_local(self, bundle, with_manifest=False, metadata={}, from_bulk=False):
        # Note, I tried to use the factory here, but could not get it to override the file for bundle.
        local = Local(
            image_server = self.image_server,
            metadata = metadata
        )
        local.save()
        file = SimpleUploadedFile(
                name=bundle,
                content=open(path.join(self.fixture_path, bundle), 'rb').read()
            )
        if from_bulk:
            local.bundle_from_bulk.save(bundle, file)
        else:
            local.bundle = file

        local.save()

        if with_manifest:
            local.manifest = create_manifest(local)
            local.save()

        return local


    def test_bundle_upload(self):
        """ It should upload the images using a fake S3 service from moto. """
        for bundle in ['bundle.zip', 'nested_volume.zip', 'csv_meta.zip']:
            self.mock_local(bundle)
            assert bundle in [f.key for f in IngestStorage().bucket.objects.all()]

    def test_image_upload_to_s3(self):
        local = self.mock_local('bundle.zip', with_manifest=True)

        local.volume_to_s3()

        image_files = [f.key for f in local.image_server.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert f'{local.manifest.pid}/00000008.jpg' in image_files

    def test_ocr_upload_to_s3(self):
        local = self.mock_local('nested_volume.zip', with_manifest=True)

        local.volume_to_s3()

        ocr_files = [f.key for f in local.image_server.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert f'{local.manifest.pid}/_*ocr*_/00000008.tsv' in ocr_files

    # @httpretty.httprettified(allow_net_connect=True)
    def test_ocr_upload_to_sftp(self):
        """ It should upload files via SFTP """
        httpretty.disable()
        local = self.mock_local('nested_volume.zip', with_manifest=True)
        local.image_server = ImageServerFactory(
            server_base='localhost',
            storage_service='sftp',
            storage_path=getcwd(),
            sftp_port=3373,
            private_key_path='/tmp/sshkey',
            sftp_user=getlogin()
        )

        _, ocr_files = local.volume_to_sftp()

        assert f'{local.manifest.pid}/_*ocr*_/00000008.tsv' in ocr_files
        rmtree(local.manifest.pid)

    def test_metadata_from_excel(self):
        """ It should create a manifest with metadata supplied in an Excel file. """
        local = self.mock_local('bundle.zip', with_manifest=True)

        assert 'pid' in local.metadata.keys()

        for key in local.metadata.keys():
            assert str(local.metadata[key]) == str(getattr(local.manifest, key))

    def test_metadata_from_csv(self):
        """ It should create a manifest with metadata supplied in a CSV file. """
        local = self.mock_local('csv_meta.zip', with_manifest=True)

        assert 'pid' in local.metadata.keys()

        for key in local.metadata.keys():
            assert local.metadata[key] == getattr(local.manifest, key)

    def test_metadata_from_tsv(self):
        """ It should create a manifest with metadata supplied in a CSV file. """
        local = self.mock_local('tsv.zip', with_manifest=True)

        assert 'pid' in local.metadata.keys()

        for key in local.metadata.keys():
            assert local.metadata[key] == getattr(local.manifest, key)

    def test_no_metadata_file(self):
        """ It should create a Manifest even when no metadata file is supplied. """
        local = self.mock_local('no_meta_file.zip', with_manifest=True)

        assert isinstance(local.manifest.pid, str)
        assert len(local.manifest.pid) == 8

    def test_single_image(self):
        """ It should work when only one image is present. """
        local = self.mock_local('single-image.zip', with_manifest=True)

        local.volume_to_s3()

        image_files = [f.key for f in local.image_server.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert f'{local.manifest.pid}/0011.jpg' in image_files

    def test_removing_junk(self):
        """
        Any hidden files should not be uploaded.
        """
        local = self.mock_local('bundle_with_junk.zip', with_manifest=True)

        local.volume_to_s3()
        local.volume_to_s3()

        ingest_files = [f.key for f in local.image_server.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert 'ocr/.junk.tsv' in local.file_list
        assert 'images/.00000010.jpg' in local.file_list
        assert f'{local.manifest.pid}/00000009.jpg' in ingest_files
        assert f'{local.manifest.pid}/.00000010.jpg' not in ingest_files
        assert f'{local.manifest.pid}/_*ocr*_/00000003.tsv' in ingest_files
        assert f'{local.manifest.pid}/_*ocr*_/.junk.tsv' not in ingest_files

    def test_removing_underscores(self):
        """
        Any hidden files should be removed.
        """
        local = self.mock_local('bundle_with_underscores.zip', with_manifest=True)

        local.volume_to_s3()

        ingest_files = [f.key for f in local.image_server.bucket.objects.filter(Prefix=local.manifest.pid)]

        underscore_files = [f for f in local.file_list if '_' in f]
        assert len(underscore_files) == 10
        assert len([f for f in local.file_list if '-' in f]) == 0
        for underscore in [f for f in local.file_list if '_' in f]:
            assert underscore not in ingest_files

    def test_when_metadata_in_filename(self):
        """
        Make sure it doesn't get get confused when the word "metadata" is in
        every path.
        """
        local = self.mock_local('metadata.zip', with_manifest=True)

        image_files, ocr_files = local.volume_to_s3()

        files_in_zip = local.file_list
        ingest_files = [f.key for f in local.image_server.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert 'metadata/images/' in files_in_zip
        assert all('metadata' in f for f in files_in_zip)
        assert any('.DS_Store' in f for f in files_in_zip)
        assert any('__MACOSX' in f for f in files_in_zip)
        assert any('~$metadata.xlsx' in f for f in files_in_zip)
        assert any('metadata/ocr/0001.tsv' in f for f in files_in_zip)
        assert local.metadata['pid'] == 't9wtf-sample'
        assert local.metadata['label'] == 't9wtf-sample'
        assert '~$metadata.xlsx' not in ingest_files
        assert f'{local.manifest.pid}/_*ocr*_/0001.tsv' in ocr_files
        assert f'{local.manifest.pid}/0001.jpg' in image_files
        assert len(ingest_files) == 2

    def test_when_underscore_in_pid(self):
        local = self.mock_local('no_meta_file.zip')
        local.manifest = ManifestFactory.create(
            image_server = self.image_server,
            pid='p_i_d'
        )

        local.volume_to_s3()
        local.volume_to_s3()

        ingest_files = [f.key for f in local.image_server.bucket.objects.filter(Prefix=local.manifest.pid)]

        assert all('p-i-d' in f for f in ingest_files)

    def test_creating_canvases(self):
        """
        Make sure it doesn't get get confused when the word "metadata" is in
        every path.
        """
        local = self.mock_local('bundle.zip', with_manifest=True)
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


    # def test_it_downloads_zip_when_local_bundle_path_is_not_none(self):
    #     local = self.mock_local('metadata.zip', with_manifest=True)
    #     local.local_bundle_path = 'swoop'
    #     files_in_zip = local.file_list
    #     assert 'metadata/images/' in files_in_zip
    #     assert exists(join(gettempdir(), 'metadata.zip'))
    #     assert local.local_bundle_path == join(gettempdir(), 'metadata.zip')

    # def test_it_cleans_up(self):
    #     local = self.mock_local('single-image.zip', with_manifest=True)
    #     local.local_bundle_path = 'swoop'
    #     local.zip_ref
    #     assert exists(join(gettempdir(), 'single-image.zip'))
    #     local.create_canvases()
    #     manifest = Manifest.objects.get(pk=local.manifest.id)
    #     assert manifest.canvas_set.count() == 1
    #     assert exists(join(gettempdir(), 'single-image.zip')) is False
    #     try:
    #         Local.objects.get(pk=local.id)
    #     except Local.DoesNotExist:
    #         pass

    def test_it_creates_mainfest_with_metadata_property(self):
        metadata = {
            'pid': '808',
            'title': 'Goodie Mob'
        }
        local = self.mock_local('no_meta_file.zip', metadata=metadata)
        local.manifest = create_manifest(local)
        assert local.manifest.pid == '808'
        assert local.manifest.title == 'Goodie Mob'

    def test_moving_bulk_bundle_to_s3(self):
        """
        It should upload Local.bundle_from_bulk to mock S3 by saving it to
        Local.bundle, then it should clean up tempfiles
        """
        # Make sure local with from_bulk is mocked correctly
        local = self.mock_local('bundle.zip', from_bulk=True)
        assert bool(local.bundle_from_bulk) is True
        bulk_name = local.bundle_from_bulk.name
        bulk_path = local.bundle_from_bulk.path
        dir_path = bulk_path[0:bulk_path.rindex('/')]
        assert bulk_name[bulk_name.rindex('/')+1:] == 'bundle.zip'
        assert path.isfile(bulk_path) is True
        assert path.isdir(dir_path) is True

        # Call bundle_to_s3() and test that it uploaded the file
        local.bundle_to_s3()
        assert bool(local.bundle) is True
        assert local.bundle.name[local.bundle.name.rindex('/')+1:] == 'bundle.zip'
        assert local.bundle.storage.exists(f'bulk/{local.id}/bundle.zip') # pylint: disable=no-member

        # Test tempfile cleanup
        assert bool(local.bundle_from_bulk) is False
        assert path.isfile(bulk_path) is False
        assert path.isdir(dir_path) is False

    def test_bundle_to_s3_fails_for_deleted_tempfile(self):
        """
        It should raise an exception because we deleted the tempfile before
        running bundle_to_s3
        """
        local = self.mock_local('bundle.zip', from_bulk=True)
        bulk_path = local.bundle_from_bulk.path
        assert path.isfile(bulk_path) is True
        remove(bulk_path)
        assert path.isfile(bulk_path) is False
        self.assertRaises(Exception, local.bundle_to_s3)
