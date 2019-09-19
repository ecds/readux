from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.urls import reverse
import warnings
from .views import AnnotationsForPage
from .models import Annotation
from ..canvases.models import Canvas
from ..manifests.models import Manifest
from .apps import AnnotationsConfig
import json

class AnnotationTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
    
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.view = AnnotationsForPage.as_view()
        self.volume = Manifest.objects.get(pid='readux:st7r6')
        self.canvas = Canvas.objects.get(pid='fedora:emory:5622')
        self.annotations = Annotation.objects.filter(canvas=self.canvas)
    
    def test_app_config(self):
        assert AnnotationsConfig.verbose_name == 'Annotations'
        assert AnnotationsConfig.name == 'apps.iiif.annotations'

    def test_get_annotations_for_page(self):
        kwargs = {'vol': self.volume.pid, 'page': self.canvas.pid, 'version': 'v2'}
        url = reverse('page_annotations', kwargs=kwargs)
        response = self.client.get(url)
        annotations = json.loads(response.content.decode('UTF-8-sig'))
        assert len(annotations) == self.annotations.count()
        assert response.status_code == 200

    def test_order(self):
        a = []
        for o in self.annotations.values('order'): 
            a.append(o['order'])
        b = a.copy()
        a.sort()
        assert a == b

