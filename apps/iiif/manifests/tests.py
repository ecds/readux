from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from .views import ManifestDetail
from .models import Manifest
from iiif_prezi.loader import ManifestReader
import json
import logging

logger = logging.getLogger(__name__)

class AnnotationTests(APITestCase):
    factory = APIRequestFactory()
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']

    def test_validate_iiif(self):
        view = ManifestDetail.as_view()
        manifest = Manifest.objects.all().first()
        manifest_uri = '/'.join(['/iiif', 'v2', manifest.pid, 'manifest']) 
        response = self.client.get(manifest_uri)
        reader = ManifestReader(response.content, version='2.1')
        try:
            mf = reader.read()
            assert mf.toJSON()
        except Exception as error:
            raise Exception(error)
