from apps.readux.tests.test_export import User
from django.core import files
from apps.ingest.forms import BulkVolumeUploadForm
from os import  environ
from os.path import join
import boto3
from django.test.client import RequestFactory
from moto import mock_s3
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django_celery_results.models import TaskResult
from django.http import HttpResponseRedirect
from django.conf import settings
from celery.contrib.pytest import celery_app
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from apps.ingest.models import Bulk, Local, Remote, IngestTaskWatcher
from apps.ingest.admin import BulkAdmin, LocalAdmin, RemoteAdmin
from .factories import BulkFactory, LocalFactory, RemoteFactory

@mock_s3
class IngestAdminTest(TestCase):
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = join(settings.APPS_DIR, 'ingest/fixtures/')

        self.image_server = ImageServerFactory(
            server_base='http://images.readux.ecds.emory',
            storage_service='s3',
            storage_path='readux'
        )

        self.user = get_user_model().objects.create_superuser(
            'adminuser', 'myemail@test.com', password='top_secret'
        )

        # Create fake bucket for moto's mock S3 service.
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket='readux')
        conn.create_bucket(Bucket='readux-ingest')

    def test_local_admin_save(self):
        """It should add a manifest to the Local object"""
        local = LocalFactory.create()

        assert local.manifest is None

        filepath = join(settings.APPS_DIR, 'ingest/fixtures/bundle.zip')

        with open(filepath, 'rb') as f:
            content = files.base.ContentFile(f.read())

        bundle_file = files.File(content.file, 'bundle.zip')

        data = { 'bundle': [bundle_file] }
        request_factory = RequestFactory()
        req = request_factory.post('/admin/ingest/local/add/', data=data)
        req.user = self.user

        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        local_model_admin.save_model(obj=local, request=req, form=None, change=None)

        local.refresh_from_db()
        assert local.manifest is not None
        # assert local.manifest.canvas_set.count() == 10

    def test_local_admin_response_add(self):
        """It should redirect to new manifest"""

        local = LocalFactory.create(manifest=ManifestFactory.create())

        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        response = local_model_admin.response_add(obj=local, request=None)

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == f'/admin/manifests/manifest/{local.manifest.id}/change/'

    def test_remote_admin_save(self):
        """It should add a manifest to the Local object"""
        remote = RemoteFactory.create(
            remote_url='https://dooley.net/manifest.json' # pylint: disable=line-too-long
        )
        assert remote.manifest is None

        remote_model_admin = RemoteAdmin(model=Remote, admin_site=AdminSite())
        remote_model_admin.save_model(obj=remote, request=None, form=None, change=None)

        remote.refresh_from_db()
        assert remote.manifest is not None

    def test_remote_admin_response_add(self):
        """It should redirect to new manifest"""

        remote = RemoteFactory.create(
            manifest=ManifestFactory.create(),
            remote_url='https://poop.org/manifest.json' # pylint: disable=line-too-long
        )

        remote_model_admin = RemoteAdmin(model=Remote, admin_site=AdminSite())
        response = remote_model_admin.response_add(obj=remote, request=None)

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == f'/admin/manifests/manifest/{remote.manifest.id}/change/'

    def test_bulk_admin_save(self):
        """It should add a Local object to this Bulk object"""
        bulk = BulkFactory.create()

        assert len(bulk.local_uploads.all()) == 0

        request_factory = RequestFactory()
        req = request_factory.post('/admin/ingest/bulk/add/')
        req.user = self.user

        bulk_model_admin = BulkAdmin(model=Bulk, admin_site=AdminSite())
        mock_form = BulkVolumeUploadForm()
        req.FILES['volume_files'] = bulk.volume_files
        bulk_model_admin.save_model(obj=bulk, request=req, form=mock_form, change=None)

        bulk.refresh_from_db()
        assert len(bulk.local_uploads.all()) == 1

    def test_bulk_admin_save_multiple(self):
        """It should add three Local objects to this Bulk object"""
        bulk = BulkFactory.create()

        assert len(bulk.local_uploads.all()) == 0

        # Add 3 files to POST request
        data = {}
        file_list = [bulk.volume_files]
        filepath2 = join(settings.APPS_DIR, 'ingest/fixtures/bundle_with_underscores.zip')
        with open(filepath2, 'rb') as f:
            content1 = files.base.ContentFile(f.read())
        file2 = files.File(content1.file, 'bundle_with_underscores.zip')
        filepath3 = join(settings.APPS_DIR, 'ingest/fixtures/no_meta_file.zip')
        with open(filepath3, 'rb') as f:
            content2 = files.base.ContentFile(f.read())
        file3 = files.File(content2.file, 'no_meta_file.zip')
        file_list.append(file2)
        file_list.append(file3)
        data['volume_files'] = file_list

        request_factory = RequestFactory()
        req = request_factory.post('/admin/ingest/bulk/add/', data=data)
        req.user = self.user

        bulk_model_admin = BulkAdmin(model=Bulk, admin_site=AdminSite())
        mock_form = BulkVolumeUploadForm()
        bulk_model_admin.save_model(obj=bulk, request=req, form=mock_form, change=None)

        bulk.refresh_from_db()
        assert len(bulk.local_uploads.all()) == 3

    def test_bulk_admin_response_add(self):
        """It should delete the Bulk object and redirect to manifests list"""

        bulk = BulkFactory.create()
        bulk_model_admin = BulkAdmin(model=Bulk, admin_site=AdminSite())
        response = bulk_model_admin.response_add(obj=bulk, request=None)

        with self.assertRaises(Bulk.DoesNotExist):
            bulk.refresh_from_db()
        assert isinstance(response, HttpResponseRedirect)
        assert response.url == '/admin/manifests/manifest/?o=-4'

    def test_bulk_admin_with_external_metadata(self):
        """It should add the metadata to the matching Local object"""
        bulk = BulkFactory.create()

        data = {}
        data['volume_files'] = []

        # Mock upload metadata csv with matching pid for zip
        filepath1 = join(settings.APPS_DIR, 'ingest/fixtures/metadata.csv')
        with open(filepath1, 'rb') as open_file:
            content1 = files.base.ContentFile(open_file.read())
        file1 = files.File(content1.file, 'metadata.csv')
        data['volume_files'].append(file1)

        # Mock upload a zip with no metadata
        filepath2 = join(settings.APPS_DIR, 'ingest/fixtures/no_meta_file.zip')
        with open(filepath2, 'rb') as open_file:
            content2 = files.base.ContentFile(open_file.read())
        file2 = files.File(content2.file, 'no_meta_file.zip')
        data['volume_files'].append(file2)

        request_factory = RequestFactory()
        req = request_factory.post('/admin/ingest/bulk/add/', data=data)
        req.user = self.user

        bulk_model_admin = BulkAdmin(model=Bulk, admin_site=AdminSite())
        mock_form = BulkVolumeUploadForm()
        bulk_model_admin.save_model(obj=bulk, request=req, form=mock_form, change=None)

        bulk.refresh_from_db()

        local = bulk.local_uploads.first()
        assert local.metadata is not None
        assert isinstance(local.metadata, dict)
        assert len(local.metadata) != 0
        assert local.metadata['pid'] == 'no_meta_file'

    # def test_local_admin_save_update_manifest(self):
    #     """It should add a manifest to the Local object"""
    #     local = LocalFactory.create()

    #     assert local.manifest is None

    #     request_factory = RequestFactory()

    #     with open(join(self.fixture_path, 'no_meta_file.zip'), 'rb') as f:
    #         content = files.base.ContentFile(f.read())

    #     local.bundle = files.File(content.file, 'no_meta_file.zip')

    #     req = request_factory.post('/admin/ingest/local/add/', data={})

    #     local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
    #     local_model_admin.save_model(obj=local, request=req, form=None, change=None)

    #     local.refresh_from_db()

    #     assert local.manifest is not None
    #     assert not local.manifest.label

    #     manifest = local.manifest
    #     new_label = Faker._get_faker().name()
    #     manifest.label = new_label
    #     manifest.save()

    #     assert manifest.label == new_label

    #     create_canvas_form_local_task(local.id)
    #     manifest.refresh_from_db()

    #     assert manifest.label == new_label
