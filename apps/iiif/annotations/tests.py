from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.urls import reverse
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
import warnings
from .views import AnnotationsForPage
from .models import Annotation
from ..canvases.models import Canvas
from ..manifests.models import Manifest
from .apps import AnnotationsConfig
import json

User = get_user_model()

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

    def test_ocr_span(self):
        ocr = Annotation()
        ocr.oa_annotation = {"annotatedBy": {"name": "ocr"}}
        ocr.x = 100
        ocr.y = 10
        ocr.w = 100
        ocr.h = 10
        ocr.content = "Obviously you're not a golfer"
        ocr.save()
        assert ocr.content == "<span id='{pk}' data-letter-spacing='0.003232758620689655'>Obviously you're not a golfer</span>".format(pk=ocr.pk)
        assert ocr.owner == User.objects.get(username='ocr')

    def test_invalid_ocr(self):
        ocr = Annotation()
        ocr.oa_annotation = {"annotatedBy": {"name": "ocr"}}
        ocr.x = 100
        ocr.y = 10
        ocr.w = 100
        ocr.h = 10
        ocr.format = Annotation.HTML
        ocr.save()
        assert ocr.content == ''
        assert ocr.format == 'text/html'
    
    def test_annotation_string(self):
        anno = Annotation.objects.all().first()
        assert anno.__str__() == str(anno.pk)

    def test_annotation_choices(self):
        anno = Annotation()
        anno.format = Annotation.HTML
        assert anno.format == 'text/html'
        anno.format = Annotation.PLAIN
        assert anno.format == 'text/plain'
        anno.format = Annotation.OCR
        assert anno.format == 'cnt:ContentAsText'
        anno.format = Annotation.TEXT
        assert anno.format == 'dctypes:Text'
        anno.format = Annotation.COMMENTING
        assert anno.format == 'oa:commenting'
        anno.format = Annotation.PAINTING
        assert anno.format == 'sc:painting'
        assert Annotation.FORMAT_CHOICES == (('text/plain', 'plain text'), ('text/html', 'html'))
        assert Annotation.TYPE_CHOICES == (('cnt:ContentAsText', 'ocr'), ('dctypes:Text', 'text'))
        assert Annotation.MOTIVATION_CHOICES == (('oa:commenting', 'commenting'), ('sc:painting', 'painting'))

    def test_ocr_for_page(self):
        kwargs = {'vol': self.volume.pid, 'page': self.canvas.pid, 'version': 'v2'}
        url = reverse('ocr', kwargs=kwargs)
        response = self.client.get(url)
        annotations = json.loads(response.content.decode('UTF-8-sig'))['resources']
        assert len(annotations) == self.canvas.annotation_set.filter(resource_type='cnt:ContentAsText', canvas=self.canvas).count()
        assert response.status_code == 200
    
    def test_annotation_style(self):
        anno = Annotation.objects.all().first()
        assert anno.style == ".anno-{c}: {{ height: {h}px; width: {w}px; font-size: {f}px; }}".format(c=(anno.pk), h=str(anno.h), w=str(anno.w), f=str(anno.h / 1.6))

    def test_annotation_style_serialization(self):
        kwargs = {'vol': self.volume.pid, 'page': self.canvas.pid, 'version': 'v2'}
        url = reverse('ocr', kwargs=kwargs)
        response = self.client.get(url)
        serialized_anno = json.loads(response.content.decode('UTF-8-sig'))['resources'][0]
        assert serialized_anno['stylesheet']['type'] == 'CssStylesheet'
        assert serialized_anno['stylesheet']['value'].startswith(".anno-{id}".format(id=serialized_anno['@id']))

    def test_serialize_list_of_annotations(self):
        data = json.loads(serialize('annotation_list', [self.canvas], is_list = True, owners = User.objects.all()))
        assert data[0]['@type'] == 'sc:AnnotationList'
        assert isinstance(data, list)
