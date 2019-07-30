from django.test import TestCase, Client
from django.test import RequestFactory
from django.urls import reverse
from .views import ManifestDetail
from .models import Manifest
from iiif_prezi.loader import ManifestReader
import json
import logging

logger = logging.getLogger(__name__)

class AnnotationTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']

    def setUp(self):
        fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
        self.factory = RequestFactory()
        self.client = Client()

    def test_validate_iiif(self):
        view = ManifestDetail.as_view()
        volume = Manifest.objects.all().first()
        kwargs = { 'pid': volume.pid, 'version': 'v2' }
        url = reverse('ManifestRender', kwargs=kwargs)
        response = self.client.get(url)
        manifest = json.loads(response.content.decode('UTF-8-sig'))
        reader = ManifestReader(response.content, version='2.1')
        try:
            mf = reader.read()
            assert mf.toJSON()
        except Exception as error:
            raise Exception(error)

        assert manifest['@id'] == "%s/manifest" % (volume.baseurl)
        assert manifest['label'] == volume.label
        assert manifest['description'] == volume.summary
        assert manifest['thumbnail']['@id'] == "%s/%s/full/600,/0/default.jpg" % (volume.canvas_set.all().first().IIIF_IMAGE_SERVER_BASE, volume.canvas_set.all().first().pid)
        assert manifest['sequences'][0]['startCanvas'] == volume.start_canvas
