# pylint: disable = missing-function-docstring, invalid-name, line-too-long
"""Test cases for :class:`apps.iiif.annotations`."""
from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
from ..views import AnnotationsForPage
from ..models import Annotation
from ..apps import AnnotationsConfig
from ...canvases.models import Canvas
from ...manifests.models import Manifest
from bs4 import BeautifulSoup
from io import StringIO
import warnings
import json

USER = get_user_model()

class AnnotationTests(TestCase):
    """Annotation test cases."""
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.view = AnnotationsForPage.as_view()
        self.volume = Manifest.objects.get(pid='readux:st7r6')
        self.canvas = Canvas.objects.get(pid='fedora:emory:5622')
        self.annotations = Annotation.objects.filter(canvas=self.canvas)

    def test_app_config(self): # pylint: disable = no-self-use
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
        assert ocr.content == "<span id='{pk}' class='anno-{pk}' data-letter-spacing='0.003232758620689655'>Obviously you're not a golfer</span>".format(pk=ocr.pk)
        assert ocr.owner == USER.objects.get(username='ocr')

    def test_default_content(self):
        ocr = Annotation()
        ocr.oa_annotation = {"annotatedBy": {"name": "ocr"}}
        ocr.x = 100
        ocr.y = 10
        ocr.w = 100
        ocr.h = 10
        ocr.format = Annotation.HTML
        ocr.save()
        assert '> </span>' in ocr.content

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
        assert anno.style == ".anno-{c}: {{ height: {h}px; width: {w}px; font-size: {f}px; letter-spacing: 15.125px;}}".format(c=(anno.pk), h=str(anno.h), w=str(anno.w), f=str(anno.h / 1.6))

    def test_annotation_style_serialization(self):
        kwargs = {'vol': self.volume.pid, 'page': self.canvas.pid, 'version': 'v2'}
        url = reverse('ocr', kwargs=kwargs)
        response = self.client.get(url)
        serialized_anno = json.loads(response.content.decode('UTF-8-sig'))['resources'][0]
        assert serialized_anno['stylesheet']['type'] == 'CssStylesheet'
        assert serialized_anno['stylesheet']['value'].startswith(".anno-{id}".format(id=serialized_anno['@id']))

    def test_serialize_list_of_annotations(self):
        data = json.loads(serialize('annotation_list', [self.canvas], is_list=True, owners=USER.objects.all()))
        assert data[0]['@type'] == 'sc:AnnotationList'
        assert isinstance(data, list)

    def test_ocr_char_with_zero_width(self):
        ocr = Annotation()
        ocr.oa_annotation = {"annotatedBy": {"name": "ocr"}}
        ocr.x = 100
        ocr.y = 10
        ocr.w = 0
        ocr.h = 10
        ocr.content = 'nice marmot'
        ocr.format = Annotation.HTML
        ocr.save()
        assert ocr.content == "<span id='{a}' class='anno-{a}' data-letter-spacing='0'>nice marmot</span>".format(a=ocr.id)
        assert ocr.style == ".anno-{a}: {{ height: 10px; width: 0px; font-size: 6.25px; letter-spacing: 0px;}}".format(a=ocr.id)
        assert ocr.format == 'text/html'

    def test_ocr_char_with_zero_height(self):
        ocr = Annotation()
        ocr.oa_annotation = {"annotatedBy": {"name": "ocr"}}
        ocr.x = 100
        ocr.y = 10
        ocr.w = 10
        ocr.h = 0
        ocr.content = 'nice marmot'
        ocr.format = Annotation.HTML
        ocr.save()
        assert ocr.content == "<span id='{a}' class='anno-{a}' data-letter-spacing='0.09090909090909091'>nice marmot</span>".format(a=ocr.id)
        assert ocr.style == ".anno-{a}: {{ height: 0px; width: 10px; font-size: 0.0px; letter-spacing: 0.9090909090909091px;}}".format(a=ocr.id)
        assert ocr.format == 'text/html'

    def test_command_output_remove_empty_ocr(self):
        anno_count = self.annotations.count()
        # anno = self.annotations[1]
        # anno.content = ' '
        # anno.save()
        out = StringIO()
        call_command('remove_empty_ocr', stdout=out)
        assert 'Empty OCR annotations have been removed' in out.getvalue()
        # assert anno_count > self.annotations.count()

    def test_resaving_ocr_annotation(self):
        # Span should not change
        anno = Annotation.objects.all().first()
        orig_span = anno.content
        anno.save()
        anno.refresh_from_db()
        assert orig_span == anno.content
        assert anno.content.startswith('<span')
        assert BeautifulSoup(anno.content, 'html.parser').span.span is None
