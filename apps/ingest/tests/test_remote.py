""" Tests for Remote Ingests """
import os
import httpretty
from django.test import TestCase
from django.conf import settings
from apps.iiif.manifests.tests.factories import ManifestFactory
from .factories import RemoteFactory
from ..services import (clean_metadata, create_manifest, get_associated_meta,
                       get_metadata_from, normalize_header)


class RemoteTest(TestCase):
    """ Tests for ingest.models.Remote """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')

    @httpretty.httprettified(allow_net_connect=False)
    def test_metadata_from_remote_manifest(self):
        """ It should extract properties from remote IIIF manifest. """
        body = None
        with open(os.path.join(self.fixture_path, 'manifest.json'), 'r') as file:
            body = file.read()

        httpretty.register_uri(
            httpretty.GET,
            'https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json',
            body=body.replace('\n', ''),
            content_type="text/json"
        )

        remote = RemoteFactory.create(
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

    # @httpretty.httprettified(allow_net_connect=True)
    def test_create_canvases_from_remote_manifest(self):
        """ It should extract properties from remote IIIF manifest. """

        manifest = ManifestFactory.create(canvases=None)
        httpretty.enable(allow_net_connect=True)
        body = None
        with open(os.path.join(self.fixture_path, 'manifest.json'), 'r') as file:
            body = file.read()

        httpretty.register_uri(
            httpretty.GET,
            'https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json',
            body=body.replace('\n', ''),
            content_type="text/json"
        )

        remote = RemoteFactory.create(
            remote_url='https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json', # pylint: disable=line-too-long
            manifest=manifest
        )

        remote.create_canvases()
        self.assertEqual(remote.manifest.canvas_set.count(), 6)

        httpretty.disable()

    def test_heidelberg_manifest(self):
        manifest = ManifestFactory.create(canvases=None)
        httpretty.enable(allow_net_connect=True)

        body = None
        with open(os.path.join(self.fixture_path, 'heidelberg.json'), 'r') as file:
            body = file.read()

        httpretty.register_uri(
            httpretty.GET,
            'https://digi.ub.uni-heidelberg.de/diglit/iiif/ferrerio1655bd2/manifest',
            body=body.replace('\n', ''),
            content_type="text/json"
        )

        remote = RemoteFactory.create(
            remote_url='https://digi.ub.uni-heidelberg.de/diglit/iiif/ferrerio1655bd2/manifest', # pylint: disable=line-too-long
            manifest=manifest
        )

        remote.open_metadata()
        assert remote.metadata['pid'] == 'ferrerio1655bd2'
        assert remote.metadata['label'] == "Nvovi Disegni Dell' Architettvre, E Piante De Palazzi Di Roma De Piv Celebri Architetti"
        assert remote.metadata['summary'] == "Nvovi Disegni Dell' Architettvre, E Piante De Palazzi Di Roma De Piv Celebri Architetti; Universitätsbibliothek Heidelberg, C 6426-2-10 GROSS RES"
        assert remote.metadata['viewingdirection'] == 'left-to-right'
        assert remote.metadata['logo_url'] == 'https://www.ub.uni-heidelberg.de/nav4/grafik/layout/ub_logo2.gif'
        assert remote.metadata['author'] == 'Ferrerio, Pietro; Rossi, Giovanni Giacomo de  [Editor]'
        assert isinstance(remote.metadata['metadata'], list)

        remote.create_canvases()
        self.assertEqual(remote.manifest.canvas_set.count(), 61)

        httpretty.disable()

    def test_princeton_manifest(self):
        manifest = ManifestFactory.create(canvases=None)
        httpretty.enable(allow_net_connect=True)

        body = None
        with open(os.path.join(self.fixture_path, 'princeton.json'), 'r') as file:
            body = file.read()

        httpretty.register_uri(
            httpretty.GET,
            'https://figgy.princeton.edu/e38d7ebb-3ae6-4eb8-a3ef-d70b5184b005/manifest',
            body=body.replace('\n', ''),
            content_type="text/json"
        )

        remote = RemoteFactory.create(
            remote_url='https://figgy.princeton.edu/e38d7ebb-3ae6-4eb8-a3ef-d70b5184b005/manifest', # pylint: disable=line-too-long
            manifest=manifest
        )

        remote.open_metadata()
        assert remote.metadata['pid'] == 'e38d7ebb-3ae6-4eb8-a3ef-d70b5184b005'
        assert remote.metadata['label'] == "Nvova pianta et alzata della citt"
        assert remote.metadata['summary'] == "Con l'aggivunta delle nove"
        assert remote.metadata['viewingdirection'] == 'left-to-right'
        assert remote.metadata['logo_url'] == 'https://figgy.princeton.edu/assets/pul_logo_icon-7b5f9384dfa5ca04f4851c6ee9e44e2d6953e55f893472a3e205e1591d3b2ca6.png'
        assert isinstance(remote.metadata['metadata'], list)

        remote.create_canvases()
        self.assertEqual(remote.manifest.canvas_set.count(), 1)

        httpretty.disable()

    def test_nga_manifest(self):
        manifest = ManifestFactory.create(canvases=None)
        httpretty.enable(allow_net_connect=True)

        body = None
        with open(os.path.join(self.fixture_path, 'nga.json'), 'r') as file:
            body = file.read()

        httpretty.register_uri(
            httpretty.GET,
            'https://www.nga.gov/content/ngaweb/api/v1/iiif/presentation/manifest.json?cultObj:id=164652',
            body=body.replace('\n', ''),
            content_type="text/json"
        )

        remote = RemoteFactory.create(
            remote_url='https://www.nga.gov/content/ngaweb/api/v1/iiif/presentation/manifest.json?cultObj:id=164652', # pylint: disable=line-too-long
            manifest=manifest
        )

        remote.open_metadata()
        assert remote.metadata['pid'] == 'cultObj:id=164652'
        assert remote.metadata['label'] == "Autre veue du Campo Vacine"
        assert remote.metadata['summary'] == "Autre veue du Campo Vacine"
        assert remote.metadata['viewingdirection'] == 'left-to-right'
        assert remote.metadata['logo_url'] == 'https://www.nga.gov/etc/designs/ngaweb/images/nga-seal.png'
        assert isinstance(remote.metadata['metadata'], list)

        remote.create_canvases()
        self.assertEqual(remote.manifest.canvas_set.count(), 1)

        httpretty.disable()