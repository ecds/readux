"""
Test class for IIIF Manifests
"""
import json
import random
import boto3
from moto import mock_s3
from datetime import datetime
from time import sleep
from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.serializers import serialize
from allauth.socialaccount.models import SocialAccount
from iiif_prezi.loader import ManifestReader
from apps.utils.noid import encode_noid
from ..views import ManifestSitemap, ManifestRis
from ..models import Manifest, ImageServer, RelatedLink
from .factories import ManifestFactory, ImageServerFactory
from ...canvases.models import Canvas
from ...canvases.tests.factories import CanvasFactory

USER = get_user_model()

# FIXME: Extend `TestCase` to mock all HTTP requests.
class ManifestTests(TestCase):
    """Tests for IIIF Manifests"""
    fixtures = [
        'users.json',
        'kollections.json',
        'manifests.json',
        'canvases.json',
        'annotations.json'
    ]

    def setUp(self):
        # fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
        self.user = get_user_model().objects.get(pk=111)
        self.factory = RequestFactory()
        self.client = Client()
        self.volume = ManifestFactory.create(
            publisher='ECDS',
            published_city='Atlanta'
        )
        for num in [1, 2, 3]:
            CanvasFactory.create(
                pid=str(random.randrange(2000, 5000)),
                manifest=self.volume,
                position=num
            )
        self.volume.save()
        self.start_canvas = self.volume.start_canvas
        self.default_start_canvas = self.volume.canvas_set.filter(is_starting_page=False).first()
        self.assumed_label = self.volume.label
        self.assumed_pid = self.volume

    # TODO: disabled until we move to proper IIIF 3
    # def test_validate_iiif(self):
    #     # volume = Manifest.objects.all().first()
    #     manifest = json.loads(
    #         serialize(
    #             'manifest',
    #             [self.volume],
    #             version='v2',
    #             annotators='Tom',
    #             exportdate=datetime.utcnow()
    #         )
    #     )
    #     reader = ManifestReader(json.dumps(manifest), version='2.1')
    #     try:
    #         manifest_reader = reader.read()
    #         assert manifest_reader.toJSON()
    #     except Exception as error:
    #         raise Exception(error)

    #     assert manifest['@id'] == "%s/manifest" % (self.volume.baseurl)
    #     assert manifest['label'] == self.volume.label
    #     assert manifest['description'] == self.volume.summary
    #     assert manifest['thumbnail']['@id'] == '{h}/{c}/full/600,/0/default.jpg'.format(
    #         h=self.volume.image_server.server_base,
    #         c=self.start_canvas.resource
    #     )
    #     assert manifest['sequences'][0]['startCanvas'] == self.volume.start_canvas.identifier

    def test_properties(self):
        assert self.volume.publisher_bib == "Atlanta : ECDS"
        assert self.volume.logo.url.endswith('/media/logos/ecds.png')
        assert self.volume.baseurl.endswith("/iiif/v2/%s" % (self.volume.pid))
        assert self.volume.start_canvas.identifier.endswith("/iiif/%s/canvas/%s" % (self.volume.pid, self.start_canvas.pid))

    def test_default_start_canvas(self):
        image_server = ImageServerFactory.create(server_base="https://fake.info")
        manifest = Manifest(image_server=image_server)
        manifest.save()
        assert manifest.start_canvas is None
        canvas = CanvasFactory.create(manifest=manifest)
        canvas.save()
        manifest.save()
        manifest.refresh_from_db()
        assert manifest.start_canvas == canvas

    def test_meta(self):
        assert str(self.volume) == self.assumed_label

    def test_sitemap(self):
        sm = ManifestSitemap()
        assert len(sm.items()) == Manifest.objects.all().count()
        assert sm.location(self.volume) == "/iiif/v2/%s/manifest" % (self.volume.pid)

    def test_ris_view(self):
        ris = ManifestRis()
        assert ris.get_context_data(volume=self.assumed_pid.pid)['volume'] == self.volume

    def test_plain_export_view(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('PlainExport', kwargs=kwargs)
        response = self.client.get(url)
        assert response.status_code == 200

    def test_autocomplete_label(self):
        assert Manifest.objects.all().first().autocomplete_label() == Manifest.objects.all().first().label

    def test_absolute_url(self):
        assert Manifest.objects.all().first().get_absolute_url() == "%s/volume/%s" % (settings.HOSTNAME, Manifest.objects.all().first().pid)

    # def test_manifest_search_vector_exists(self):
    #     assert self.volume.search_vector is None
    #     self.volume.save()
    #     self.volume.refresh_from_db()
    #     assert self.volume.search_vector is not None

    def test_multiple_starting_canvases(self):
        volume = ManifestFactory.create()
        for index, _ in enumerate(range(4)):
            CanvasFactory.create(manifest=volume, is_starting_page=True, position=index+1)
            sleep(2)
        # volume.refresh_from_db()
        manifest = json.loads(
            serialize(
                'manifest',
                [volume],
                version='v2',
                annotators='Tom',
                exportdate=datetime.utcnow()
            )
        )
        first_canvas = volume.canvas_set.all().order_by('position').first()
        assert volume.start_canvas.pid in manifest['thumbnail']['@id']

    def test_no_starting_canvases(self):
        manifest = ManifestFactory.create()
        try:
            manifest.canvas_set.all().get(is_starting_page=True)
        except Canvas.DoesNotExist as error:
            assert str(error) == 'Canvas matching query does not exist.'
        manifest.refresh_from_db()
        serialized_manifest = json.loads(
            serialize(
                'manifest',
                [manifest]
            )
        )
        assert manifest.canvas_set.all().first().pid in serialized_manifest['thumbnail']['@id']

    def test_default_iiif_image_server_url(self):
        image_server = ImageServer()
        assert image_server.server_base == settings.IIIF_IMAGE_SERVER_BASE

    def test_serialized_related_links(self):
        """ It should add a list of links for the "seeAlso" key. """
        manifest = ManifestFactory.create()
        no_links = json.loads(
            serialize(
                'manifest',
                [manifest]
            )
        )
        assert not no_links['seeAlso']

        link = RelatedLink(link='images.org', manifest=manifest, is_structured_data=True)
        link.save()
        manifest.refresh_from_db()

        with_links = json.loads(
            serialize(
                'manifest',
                [manifest]
            )
        )

        assert 'seeAlso' in with_links.keys()
        assert isinstance(with_links['seeAlso'], list)
        assert len(with_links['seeAlso']) == 1
        assert with_links['seeAlso'][0] == 'images.org'

    @mock_s3
    def test_renameing_pid_when_images_are_in_s3(self):
        """ It should copy the canvas files to a folder with new pid and delete old pid. """
        image_server = ImageServerFactory.create(storage_path='earthgang', storage_service='s3')
        manifest = ManifestFactory(image_server=image_server)
        conn = boto3.resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket=image_server.storage_path)
        original_pid = manifest.pid
        image_server.bucket.upload_file('apps/iiif/canvases/fixtures/00000002.jpg', f'{manifest.pid}/00000002.jpg')
        assert f'{manifest.pid}/00000002.jpg' in [f.key for f in image_server.bucket.objects.all()]
        manifest.pid = encode_noid(0)
        manifest.save()
        manifest.refresh_from_db()
        assert f'{original_pid}/00000002.jpg' not in [f.key for f in image_server.bucket.objects.all()]
        assert original_pid not in [f.key for f in image_server.bucket.objects.all()]
        assert f'{manifest.pid}/00000002.jpg' in [f.key for f in image_server.bucket.objects.all()]
