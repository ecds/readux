from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.urls import reverse
import warnings
from .views import AnnotationsForPage
from .models import Annotation
from ..canvases.models import Canvas
import json

class AnnotationTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
    
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.view = AnnotationsForPage.as_view()

    def test_get_annotations_for_page(self):
        kwargs = {'vol': 'readux:st7r6', 'page': 'fedora:emory:5622', 'version': 'v2'}
        url = reverse('page_annotations', kwargs=kwargs)
        response = self.client.get(url)
        annotations = json.loads(response.content.decode('UTF-8-sig'))
        assert len(annotations) == len(Annotation.objects.filter(canvas=Canvas.objects.get(pid=kwargs['page'])))
        assert response.status_code == 200    
