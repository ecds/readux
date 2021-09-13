""" Tests for ingest.services """
import os
import json
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
import apps.ingest.services as services
from .factories import RemoteFactory

class ServicesTest(TestCase):
    """ Tests for ingest.services """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')

    def test_cleaning_metadata(self):
        """ It should normalize keys and remove key/value pairs that
        do not match a Manifest field. """
        fake_metadata = {
            'pid': 'blm',
            'invalid': 'trump',
            'summary': 'idk',
            'PUBLISHER': 'ecds',
            'Published City': 'atlanta'
        }

        cleaned_metadata = services.clean_metadata(fake_metadata)

        manifest_fields = [f.name for f in Manifest._meta.get_fields()]

        for key in cleaned_metadata.keys():
            assert key in manifest_fields

        assert 'Published City' not in cleaned_metadata.keys()
        assert 'PUBLISHER' not in cleaned_metadata.keys()
        assert 'invalid' not in cleaned_metadata.keys()
        assert cleaned_metadata['published_city'] == fake_metadata['Published City']
        assert cleaned_metadata['publisher'] == fake_metadata['PUBLISHER']

    def test_extracting_image_server_with_port(self):
        """ If should return a URL with a specified port. """
        canvas = {
            'images': [{
                'resource': {
                    'service': {
                        '@id': "https://readux.org:8000/iiif/readux:thgg7_1.jp2"
                    }
                }
            }]
        }
        image_server_url = services.extract_image_server(canvas)
        assert image_server_url == 'https://readux.org:8000/iiif'

    def test_extracting_image_server_without_port(self):
        """ If should return a URL with no port. """
        canvas = {
            'images': [{
                'resource': {
                    'service': {
                        '@id': "https://readux.org/iiif/readux:thgg7_1.jp2"
                    }
                }
            }]
        }
        image_server_url = services.extract_image_server(canvas)
        assert image_server_url == 'https://readux.org/iiif'

    def test_adding_related_link_to_remote_ingest_manifest(self):
        remote = RemoteFactory.create(
            remote_url='https://swoop.net/manifest.json' # pylint: disable=line-too-long
        )
        manifest = services.create_manifest(remote)
        related_link = manifest.relatedlink_set.first()
        assert related_link.link == remote.remote_url

    def test_parse_v2_manifest_with_label_as_list(self):
        data = json.loads(open(os.path.join(settings.APPS_DIR, 'ingest/fixtures/manifest-label-as-array.json')).read())
        metadata = services.parse_iiif_v2_manifest(data)
        self.assertEqual(metadata['label'], 'Address by American Hero Frederick Douglass')
