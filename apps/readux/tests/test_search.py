"""Test searching volume content."""
from itertools import repeat
from random import randrange
import json
from django.test import TestCase, Client
from django.test import RequestFactory
from django.urls import reverse
from apps.users.tests.factories import UserFactory
from ...iiif.manifests.tests.factories import ManifestFactory
from ...iiif.canvases.tests.factories import CanvasFactory
from ...iiif.annotations.tests.factories import AnnotationFactory
from ..search import SearchManifestCanvas
from .factories import UserAnnotationFactory


class TestReaduxPageDetailSearch(TestCase):
    """
    Test page search.
    """
    def setUp(self):
        self.search_manifest_view = SearchManifestCanvas.as_view()
        self.request = RequestFactory()
        self.volume = ManifestFactory.create()
        original_canvas = self.volume.canvas_set.first()
        self.user = UserFactory.create()
        self.ocr_user = UserFactory.create(username='ocr', name='OCR')
        canvas_position = 1
        for _ in repeat(None, randrange(5, 10)):
            CanvasFactory.create(manifest=self.volume, position=canvas_position)
            canvas_position += 1
        self.volume.start_canvas = self.volume.canvas_set.all()[1]
        self.volume.save()
        # # Delete the canvas created by the ManifestFactory to ensure a clean set.
        original_canvas.delete()
        for _ in [1, 2]:
            self.add_annotations(self.volume.canvas_set.get(position=1))
        for _ in [1, 2, 3]:
            self.add_annotations(self.volume.canvas_set.get(position=2))

        # pylint: enable = unused-variable

        self.client = Client()
        self.url = reverse('search_pages')

    def add_annotations(self, canvas):
        """Add OCR and User annotations to a canvas."""
        AnnotationFactory.create(
            canvas=canvas,
            content='stankonia',
            owner=self.ocr_user
        )
        UserAnnotationFactory.create(
            canvas=canvas,
            content='Aquemini',
            owner=self.user
        )

    def load_results(self, response):
        """Decode the json response
        :param response: search results
        :type response: client response
        :return: Dict of results
        :rtype: dict
        """
        return json.loads(response.content.decode('UTF-8-sig'))

    def test_manifest_canvas_ocr_partial_search(self):
        query_params = {'volume': self.volume.pid, 'type': 'partial', 'query': 'stank'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = UserFactory.create()
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert len(search_results['ocr_annotations']) == 2
        assert len(search_results['user_annotations']) == 0
        assert search_results['search_terms'] == 'stank'.split()
        assert json.loads(search_results['ocr_annotations'][0])['canvas__position'] == 1
        assert json.loads(search_results['ocr_annotations'][1])['canvas__position'] == 2
        assert json.loads(search_results['ocr_annotations'][0])['canvas__position__count'] == 2
        assert json.loads(search_results['ocr_annotations'][1])['canvas__position__count'] == 3

    def test_manifest_canvas_ocr_exact_search(self):
        query_params = {'volume': self.volume.pid, 'type': 'exact', 'query': 'stankonia'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = UserFactory.create()
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert len(search_results['ocr_annotations']) == 2
        assert len(search_results['user_annotations']) == 0
        assert json.loads(search_results['ocr_annotations'][0])['canvas__position'] == 1
        assert json.loads(search_results['ocr_annotations'][1])['canvas__position'] == 2
        assert json.loads(search_results['ocr_annotations'][0])['canvas__position__count'] == 2
        assert json.loads(search_results['ocr_annotations'][1])['canvas__position__count'] == 3

    def test_manifest_canvas_ocr_exact_search_no_results(self):
        query_params = {'volume': self.volume.pid, 'type': 'exact', 'query': 'Idlewild'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = UserFactory.create()
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert len(search_results['ocr_annotations']) == 0
        assert len(search_results['user_annotations']) == 0

    def test_manifest_canvas_user_annotation_partial_search(self):
        query_params = {'volume': self.volume.pid, 'type': 'partial', 'query': 'Aqu'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = self.user
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert len(search_results['ocr_annotations']) == 0
        assert len(search_results['user_annotations']) == 2
        assert json.loads(search_results['user_annotations'][0])['canvas__position'] == 1
        assert json.loads(search_results['user_annotations'][1])['canvas__position'] == 2

    def test_manifest_canvas_user_annotation_exact_search(self):
        query_params = {'volume': self.volume.pid, 'type': 'exact', 'query': 'Aquemini'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = self.user
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert len(search_results['ocr_annotations']) == 0
        assert len(search_results['user_annotations']) == 2
        assert json.loads(search_results['user_annotations'][0])['canvas__position'] == 1
        assert json.loads(search_results['user_annotations'][1])['canvas__position'] == 2

    def test_manifest_canvas_user_annotation_exact_search_no_results(self):
        query_params = {'volume': self.volume.pid, 'type': 'exact', 'query': 'Idlewild'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = self.user
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert len(search_results['ocr_annotations']) == 0
        assert len(search_results['user_annotations']) == 0
