from os.path import join
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.conf import settings
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from apps.ingest.models import Local
from apps.ingest.admin import LocalAdmin
from .factories import LocalFactory

class IngestAdminTest(TestCase):
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = join(settings.APPS_DIR, 'ingest/fixtures/')

    def test_admin_save(self):
        """It should add a manifest to the Local object"""
        local = Local(
            image_server = ImageServerFactory.create()
        )
        local.bundle = SimpleUploadedFile(
            name='bundle.zip',
            content=open(join(self.fixture_path, 'bundle.zip'), 'rb').read()
        )

        assert local.manifest is None

        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        local_model_admin.save_model(obj=local, request=None, form=None, change=None)

        local.refresh_from_db()
        assert local.manifest is not None
        # assert local.manifest.canvas_set.count() == 10

    def test_admin_response_add(self):
        """It should redirect to new manifest"""

        local = LocalFactory.create(manifest=ManifestFactory.create())

        local_model_admin = LocalAdmin(model=Local, admin_site=AdminSite())
        response = local_model_admin.response_add(obj=local, request=None)

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == f'/admin/manifests/manifest/{local.manifest.id}/change/'


