""" Tests for Remote Ingests """
import os
import httpretty
from django.test import TestCase
from django.conf import settings
from ..models import Remote

class RemoteTest(TestCase):
    """ Tests for ingest.models.Remote """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')

    @httpretty.activate
    def test_metadata_from_remote_manifest(self):
        """ It should extract properties from remote IIIF manifest. """
        with open(os.path.join(self.fixture_path, 'manifest.json')) as data:
            httpretty.register_uri(
                httpretty.GET,
                'https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json',
                body=data.read(),
                content_type="text/json"
            )
            remote = Remote()
            remote.remote_url = 'https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json' # pylint: disable=line-too-long
            assert remote.metadata['pid'] == '09359080.4757.emory.edu'
            assert remote.metadata['label'] == 'Address by Hon. Frederick Douglass'
            assert remote.metadata['summary'] == 'Electronic reproduction. digitized.'
            assert remote.metadata['viewingdirection'] == 'left-to-right'
            assert remote.metadata['publisher'] == 'Baltimore : Press of Thomas & Evans'
            assert remote.metadata['attribution'] == 'The Internet Archive'
            assert isinstance(remote.metadata['metadata'], list)
            assert 'logo' not in remote.metadata
