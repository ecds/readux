"""Test searching volume content."""
from itertools import repeat
from random import randrange
import json
from django.test import TestCase, Client
from django.test import RequestFactory
from django.urls import reverse
from django_elasticsearch_dsl.test import ESTestCase
from apps.users.tests.factories import UserFactory
from ...iiif.manifests.tests.factories import ManifestFactory
from ...iiif.canvases.tests.factories import CanvasFactory
from ...iiif.annotations.tests.factories import AnnotationFactory
from ..search import SearchManifestCanvas
from .factories import UserAnnotationFactory


class TestReaduxPageDetailSearch(ESTestCase, TestCase):
    """
    Test page search.
    """
    def setUp(self):
        super().setUp()
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
            canvas = self.volume.canvas_set.get(position=1)
            self.add_annotations(canvas)
            canvas.save()
        for _ in [1, 2, 3]:
            canvas = self.volume.canvas_set.get(position=2)
            self.add_annotations(canvas)
            canvas.save()

        # pylint: enable = unused-variable

        self.client = Client()
        self.url = reverse('search_pages')

    def add_annotations(self, canvas):
        """Add OCR and User annotations to a canvas."""
        AnnotationFactory.create(
            canvas=canvas,
            content='stinking',
            owner=self.ocr_user
        )
        UserAnnotationFactory.create(
            canvas=canvas,
            content='outcasts',
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
        query_params = {'volume_id': self.volume.pid, 'keyword': 'stink'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = UserFactory.create()
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)

        # two hits in text, no hits in annotations
        assert search_results['matches_in_text']['total_matches_in_volume'] == 2
        assert search_results['matches_in_annotations']['total_matches_in_volume'] == 0
        for match in search_results['matches_in_text']['volume_matches']:
            # should be in canvas indices 1 and 2
            assert match["canvas_index"] in [1, 2]
            if match["canvas_index"] == 1:
                # 2 matches in first canvas
                # NOTE: OCR annotations are indexed as a single block of text per canvas. in this
                # case, the terms appeared so close together they are grouped into one result, but
                # still highlighted individually, thus two <em>s.
                assert match["context"][0].count("<em>") == 2
            elif match["canvas_index"] == 2:
                # 3 matches in second canvas
                assert match["context"][0].count("<em>") == 3

    def test_manifest_canvas_ocr_exact_search(self):
        query_params = {'volume_id': self.volume.pid, 'keyword': '"stinking"'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = UserFactory.create()
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        # two hits in text, no hits in annotations
        assert search_results['matches_in_text']['total_matches_in_volume'] == 2
        assert search_results['matches_in_annotations']['total_matches_in_volume'] == 0
        for match in search_results['matches_in_text']['volume_matches']:
            # should be in canvas indices 1 and 2
            assert match["canvas_index"] in [1, 2]
            if match["canvas_index"] == 1:
                # 2 matches in first canvas; so close together they are grouped into one result
                assert match["context"][0].count("<em>") == 2
            elif match["canvas_index"] == 2:
                # 3 matches in second canvas; so close together they are grouped into one result
                assert match["context"][0].count("<em>") == 3

    def test_manifest_canvas_ocr_exact_search_no_results(self):
        query_params = {'volume_id': self.volume.pid, 'keyword': '"Idlewild"'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = UserFactory.create()
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert search_results['matches_in_text']['total_matches_in_volume'] == 0
        assert search_results['matches_in_annotations']['total_matches_in_volume'] == 0

    def test_manifest_canvas_user_annotation_partial_search(self):
        query_params = {'volume_id': self.volume.pid, 'keyword': 'outcast'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = self.user
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        print(search_results)
        assert search_results['matches_in_text']['total_matches_in_volume'] == 0
        # NOTE: since user annotations are indexed individually (unlike OCR annotations which
        # are grouped by canvas), each one gets a separate hit, so the total matches is 5.
        # however, in the search results, they will be grouped by canvas. thus, len(matches) is 2,
        # one per canvas, while total matches remains 5.
        assert search_results['matches_in_annotations']['total_matches_in_volume'] == 5
        assert len(search_results['matches_in_annotations']['volume_matches']) == 2
        for match in search_results['matches_in_annotations']['volume_matches']:
            # should be in canvas indices 1 and 2
            assert match["canvas_index"] in [1, 2]

    def test_manifest_canvas_user_annotation_exact_search(self):
        query_params = {'volume_id': self.volume.pid, 'keyword': '"outcasts"'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = self.user
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        print(search_results)
        assert search_results['matches_in_text']['total_matches_in_volume'] == 0
        # NOTE: see above note about user annotations vs OCR annotations.
        assert search_results['matches_in_annotations']['total_matches_in_volume'] == 5
        assert len(search_results['matches_in_annotations']['volume_matches']) == 2
        for match in search_results['matches_in_annotations']['volume_matches']:
            # should be in canvas indices 1 and 2
            assert match["canvas_index"] in [1, 2]

    def test_manifest_canvas_user_annotation_exact_search_no_results(self):
        query_params = {'volume_id': self.volume.pid, 'keyword': '"Idlewild"'}
        request = self.request.get(
            self.url, query_params
        )
        request.user = self.user
        response = self.search_manifest_view(request)
        search_results = self.load_results(response)
        assert search_results['matches_in_text']['total_matches_in_volume'] == 0
        assert search_results['matches_in_annotations']['total_matches_in_volume'] == 0
