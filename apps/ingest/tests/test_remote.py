""" Tests for Remote Ingests """
import os
from django.test import TestCase
from django.conf import settings
from apps.iiif.manifests.tests.factories import ManifestFactory
from .factories import RemoteFactory

class RemoteTest(TestCase):
    """ Tests for ingest.models.Remote """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')

    def test_metadata_from_remote_manifest(self):
        """ It should extract properties from remote IIIF manifest. """
        remote = RemoteFactory.create(
            manifest=ManifestFactory.create(),
            remote_url='https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json' # pylint: disable=line-too-long
        )
        remote.open_metadata()
        assert remote.metadata['pid'] == '09359080.4757.emory.edu'
        assert remote.metadata['label'] == 'Address by Hon. Frederick Douglass'
        assert remote.metadata['summary'] == 'Respect Frederick Douglass.'
        assert remote.metadata['viewingdirection'] == 'left-to-right'
        assert remote.metadata['publisher'] == 'Baltimore : Press of Thomas & Evans'
        assert remote.metadata['attribution'] == 'The Internet Archive'
        assert isinstance(remote.metadata['metadata'], list)
        assert 'logo' not in remote.metadata

    def test_create_canvases_from_remote_manifest(self):
        """ It should extract properties from remote IIIF manifest. """
        manifest = ManifestFactory.create()
        for canvas in manifest.canvas_set.all():
            canvas.delete()
        remote = RemoteFactory.create(
            manifest=manifest,
            remote_url='https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json' # pylint: disable=line-too-long
        )
        remote.create_canvases()
        self.assertEqual(remote.manifest.canvas_set.count(), 6)
