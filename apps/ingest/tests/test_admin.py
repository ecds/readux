from os import  environ
from os.path import join
import boto3
from moto import mock_s3
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.conf import settings
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from apps.ingest.models import Local, Remote
from apps.ingest.admin import LocalAdmin, RemoteAdmin
from .factories import LocalFactory, RemoteFactory

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

        # Create fake bucket for moto's mock S3 service.
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket='readux')
        conn.create_bucket(Bucket='readux-ingest')

    def test_local_admin_save(self):
        """It should add a manifest to the Local object"""
        local = LocalFactory.create(local_bundle_path=join(self.fixture_path, 'bundle.zip'))

        assert local.manifest is None

        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        local_model_admin.save_model(obj=local, request=None, form=None, change=None)

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
