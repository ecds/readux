from os.path import join
from os import mkdir
from getpass import getuser
from shutil import rmtree
import boto3
import httpretty
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.core import files
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls.base import reverse
from django_celery_results.models import TaskResult
from moto import mock_s3
from apps.ingest.forms import BulkVolumeUploadForm
from apps.iiif.canvases.models import Canvas
from apps.iiif.kollections.models import Collection
from apps.iiif.kollections.tests.factories import CollectionFactory
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from apps.ingest.models import Bulk, Local, Remote, IngestTaskWatcher
from apps.ingest.admin import BulkAdmin, LocalAdmin, RemoteAdmin, TaskWatcherAdmin
from apps.users.tests.factories import UserFactory
from .factories import BulkFactory, LocalFactory, RemoteFactory, TaskResultFactory
from .mock_sftp import MockSFTP

@mock_s3
class IngestAdminTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sftp_server = MockSFTP()

    @classmethod
    def tearDownClass(cls):
        cls.sftp_server.stop_server()

    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = join(settings.APPS_DIR, 'ingest/fixtures/')

        self.s3_image_server = ImageServerFactory(
            server_base='http://images.readux.ecds.emory',
            storage_service='s3',
            storage_path='readux'
        )

        self.sftp_image_server = ImageServerFactory(
            server_base=self.sftp_server.host,
            storage_service='sftp',
            storage_path='admin_images',
            sftp_port=self.sftp_server.port,
            private_key_path=self.sftp_server.key_file,
            sftp_user=getuser()
        )

        self.user = UserFactory.create(is_superuser=True)

        self.task_result = TaskResultFactory()
        self.task_watcher = IngestTaskWatcher.manager.create_watcher(
            task_id='1',
            task_result=self.task_result,
            task_creator=self.user,
            filename='test_fake.zip'
        )

        # Create fake bucket for moto's mock S3 service.
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket='readux')
        conn.create_bucket(Bucket='readux-ingest')

    def test_local_admin_save_s3(self):
        """It should add a create a manifest and canvases and delete the Local object"""
        local = LocalFactory.build(
            image_server=self.s3_image_server
        )

        original_manifest_count = Manifest.objects.count()
        original_canvas_count = Canvas.objects.count()

        request_factory = RequestFactory()

        with open(join(self.fixture_path, 'no_meta_file.zip'), 'rb') as f:
            content = files.base.ContentFile(f.read())

        local.bundle = files.File(content.file, 'no_meta_file.zip')

        req = request_factory.post('/admin/ingest/local/add/', data={})
        req.user = self.user

        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        local_model_admin.save_model(obj=local, request=req, form=None, change=None)

        # Saving should kick off the task to create the canvases and then delete
        # the `Local` ingest object when done.
        try:
            local.refresh_from_db()
            assert False
        except Local.DoesNotExist:
            assert True

        # A new `Manifest` should have been created along with the canvases
        # in the ingest
        assert Manifest.objects.count() == original_manifest_count + 1
        assert Canvas.objects.count() == original_canvas_count + 10

    def test_local_admin_save_sftp(self):
        """It should add a create a manifest and canvases and delete the Local object"""
        httpretty.disable()
        local = LocalFactory.build(
            image_server=self.sftp_image_server
        )

        mkdir(local.image_server.storage_path)

        original_manifest_count = Manifest.objects.count()
        original_canvas_count = Canvas.objects.count()

        request_factory = RequestFactory()

        with open(join(self.fixture_path, 'no_meta_file.zip'), 'rb') as f:
            content = files.base.ContentFile(f.read())

        local.bundle = files.File(content.file, 'no_meta_file.zip')

        req = request_factory.post('/admin/ingest/local/add/', data={})
        req.user = self.user

        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        local_model_admin.save_model(obj=local, request=req, form=None, change=None)

        # Saving should kick off the task to create the canvases and then delete
        # the `Local` ingest object when done.
        try:
            local.refresh_from_db()
            assert False
        except Local.DoesNotExist:
            assert True

        rmtree(local.image_server.storage_path)

        # A new `Manifest` should have been created along with the canvases
        # in the ingest
        assert Manifest.objects.count() == original_manifest_count + 1
        assert Canvas.objects.count() == original_canvas_count + 10

    def test_local_ingest_with_collections(self):
        """It should add chosen collections to the Local's manifests"""
        local = LocalFactory.build(
            image_server=self.s3_image_server
        )

        # Force evaluation to get the true current list of manifests
        manifests_before = list(Manifest.objects.all())

        # Assign collections to Local
        for _ in range(3):
            CollectionFactory.create()
        collections = Collection.objects.all()
        local.save()
        local.collections.set(collections)
        assert len(local.collections.all()) == 3

        # Make a local ingest
        request_factory = RequestFactory()
        with open(join(self.fixture_path, 'no_meta_file.zip'), 'rb') as f:
            content = files.base.ContentFile(f.read())
        local.bundle = files.File(content.file, 'no_meta_file.zip')
        req = request_factory.post('/admin/ingest/local/add/', data={})
        req.user = self.user
        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        local_model_admin.save_model(obj=local, request=req, form=None, change=None)

        # Get the newly created manifest by comparing current list to the list before
        manifests_after = list(Manifest.objects.all())
        new_manifests = [x for x in manifests_after if x not in manifests_before]
        assert len(new_manifests) == 1
        assert isinstance(new_manifests[0], Manifest)

        # The new manifest shouhld get the Local's collections
        assert new_manifests[0].collections.count() == 3

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
            remote_url='https://dooley.net/manifest.json'
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
        assert response.url == reverse('admin:ingest_ingesttaskwatcher_changelist')

    def test_bulk_admin_with_external_metadata(self):
        """It should add the metadata to the matching Local object"""
        bulk = BulkFactory.create(image_server=self.s3_image_server)

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
        assert local.metadata['label'] == 'Test Bundle'


    def test_task_watcher_admin_functions(self):
        """It should get the appropriate values from the watcher's associated TaskResult"""
        watcher = self.task_watcher
        assert isinstance(watcher.task_result, TaskResult)
        assert watcher.task_id == watcher.task_result.task_id
        assert watcher.task_result.task_name == 'fake_task'
        assert watcher.task_result.status == 'PENDING'

        watcher_admin = TaskWatcherAdmin(model=IngestTaskWatcher, admin_site=AdminSite())
        assert watcher_admin.task_name(watcher) == 'fake_task'
        assert 'PENDING' in watcher_admin.task_status(watcher)

    def test_bulk_ingest_with_collections(self):
        """It should add the collections to the matching Local object"""
        bulk = BulkFactory.create()
        for _ in range(3):
            CollectionFactory.create()
        collections = Collection.objects.all()
        bulk.save()
        bulk.collections.set(collections)
        data = {}
        data['volume_files'] = [bulk.volume_files]

        request_factory = RequestFactory()
        req = request_factory.post('/admin/ingest/bulk/add/', data=data)
        req.user = self.user

        bulk_model_admin = BulkAdmin(model=Bulk, admin_site=AdminSite())
        mock_form = BulkVolumeUploadForm()
        bulk_model_admin.save_model(obj=bulk, request=req, form=mock_form, change=None)
        bulk.refresh_from_db()
        created_local = bulk.local_uploads.first()

        assert created_local.collections.count() == 3


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
