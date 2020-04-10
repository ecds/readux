'''
'''
import json
from datetime import datetime
from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.serializers import serialize
from allauth.socialaccount.models import SocialAccount
from iiif_prezi.loader import ManifestReader
from ..views import ManifestSitemap, ManifestRis
from ..models import Manifest
from ..forms import JekyllExportForm
from .factories import ManifestFactory
from ...canvases.tests.factories import CanvasFactory

USER = get_user_model()

class ManifestTests(TestCase):
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
        self.volume = Manifest.objects.get(pk='464d82f6-6ae5-4503-9afc-8e3cdd92a3f1')
        self.start_canvas = self.volume.canvas_set.filter(is_starting_page=True).first()
        self.default_start_canvas = self.volume.canvas_set.filter(is_starting_page=False).first()
        self.assumed_label = ' Descrizione del Palazzo Apostolico Vaticano '
        self.assumed_pid = 'readux:st7r6'

    def test_validate_iiif(self):
        # view = ManifestDetail.as_view()
        volume = Manifest.objects.all().first()
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('ManifestRender', kwargs=kwargs)
        response = self.client.get(url)
        manifest = json.loads(response.content.decode('UTF-8-sig'))
        reader = ManifestReader(response.content, version='2.1')
        try:
            mf = reader.read()
            assert mf.toJSON()
        except Exception as error:
            raise Exception(error)

        assert manifest['@id'] == "%s/manifest" % (self.volume.baseurl)
        assert manifest['label'] == self.volume.label
        assert manifest['description'] == volume.summary
        assert manifest['thumbnail']['@id'] == "%s/%s/full/600,/0/default.jpg" % (self.volume.canvas_set.all().first().IIIF_IMAGE_SERVER_BASE, self.start_canvas.pid)
        assert manifest['sequences'][0]['startCanvas'] == self.volume.start_canvas

    def test_properties(self):
        assert self.volume.publisher_bib == "In Roma : Appresso Niccol\u00f2, e Marco Pagliarini ..."
        assert self.volume.thumbnail_logo.endswith("/%s/%s" % ("media", "awesome.png"))
        assert self.volume.baseurl.endswith("/iiif/v2/%s" % (self.volume.pid))
        assert self.volume.start_canvas.endswith("/iiif/%s/canvas/%s" % (self.volume.pid, self.start_canvas.pid))
    
    def test_default_start_canvas(self):
        self.start_canvas.is_starting_page = False
        self.start_canvas.save()
        assert self.volume.start_canvas.endswith("/iiif/%s/canvas/%s" % (self.volume.pid, self.default_start_canvas.pid))

    def test_meta(self):
        assert str(self.volume) == self.assumed_label

    def test_sitemap(self):
        sm = ManifestSitemap()
        assert len(sm.items()) == Manifest.objects.all().count()
        assert sm.location(self.volume) == "/iiif/v2/%s/manifest" % (self.assumed_pid)

    def test_ris_view(self):
        ris = ManifestRis()
        assert ris.get_context_data(volume=self.assumed_pid)['volume'] == self.volume

    def test_plain_export_view(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('PlainExport', kwargs=kwargs)
        response = self.client.get(url)
        assert response.status_code == 200

    def test_autocomplete_label(self):
        assert Manifest.objects.all().first().autocomplete_label() == Manifest.objects.all().first().label

    def test_absolute_url(self):
        assert Manifest.objects.all().first().get_absolute_url() == "%s/volume/%s" % (settings.HOSTNAME, Manifest.objects.all().first().pid)

    def test_form_mode_choices_no_github(self):
        form = JekyllExportForm(user=self.user)
        assert len(form.fields['mode'].choices) == 1
        assert form.fields['mode'].choices[0] != 'github'

    def test_form_mode_choices_with_github(self):
        sa = SocialAccount(provider='github', user=self.user)
        sa.save()
        form = JekyllExportForm(user=self.user)
        assert len(form.fields['mode'].choices) == 2
        assert form.fields['mode'].choices[1][0] == 'github'

    def test_manifest_search_vector_exists(self):
        assert self.volume.search_vector is None
        self.volume.save()
        self.volume.refresh_from_db()
        assert self.volume.search_vector is not None

    def test_multiple_starting_canvases(self):
        volume = ManifestFactory.create()
        for num in range(4):
            CanvasFactory.create(manifest=volume, is_starting_page=True)
        manifest = json.loads(
            serialize(
                'manifest',
                [volume],
                version='v2',
                annotators='Tom',
                exportdate=datetime.utcnow()
            )
        )
        first_canvas = volume.canvas_set.all().first()
        assert manifest['thumbnail']['@id'] == '{b}/{p}/full/600,/0/default.jpg'.format(b=first_canvas.IIIF_IMAGE_SERVER_BASE, p=first_canvas.pid)
