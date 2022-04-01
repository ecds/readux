import os
from unittest.mock import Mock
import pytest
from tempfile import gettempdir
from pathlib import Path
from django.test import RequestFactory, TestCase
from django.http import HttpResponse
from apps.readux import views
from apps.iiif.manifests.models import Language, Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.iiif.kollections.tests.factories import CollectionFactory
from apps.iiif.kollections.models import Collection
from apps.iiif.canvases.models import Canvas
from apps.users.tests.factories import UserFactory
import config.settings.local as settings
from django_elasticsearch_dsl.test import ESTestCase

pytestmark = pytest.mark.django_db

class TestReaduxViews:
    def test_page_detail_context(self):
        factory = RequestFactory()
        user = UserFactory.create()
        assert not user._state.adding
        volume = ManifestFactory.create()
        request = factory.get('/')
        request.user = user
        view = views.PageDetail(request=request)
        data = view.get_context_data(volume=volume.pid, page=volume.canvas_set.all().first().pid)
        assert data['volume'].pid == volume.pid
        assert isinstance(data['volume'], Manifest)
        assert isinstance(data['page'], Canvas)
        assert isinstance(data['user_annotation_page_count'], int)
        assert isinstance(data['user_annotation_count'], int)
        assert data['mirador_url'] == settings.MIRADOR_URL

    def test_page_detail_context_with_no_page_in_kwargs(self):
        factory = RequestFactory()
        request = factory.get('/')
        user = UserFactory.create()
        request.user = user
        volume = ManifestFactory.create()
        view = views.PageDetail(request=request)
        data = view.get_context_data(volume=volume.pid)
        assert data['volume'].pid == volume.pid
        assert data['page'].pid == volume.canvas_set.all().first().pid

    def test_manifests_sitemap(self):
        for n in range(5):
            ManifestFactory.create()
        view = views.ManifestsSitemap()
        manifest = Manifest.objects.all().first()
        assert view.items().count() == Manifest.objects.all().count()
        assert view.location(manifest) == '/volume/{m}/page/all'.format(m=manifest.pid)
        assert view.lastmod(manifest) == manifest.updated_at

    def test_collections_sitemap(self):
        for n in range(3):
            CollectionFactory.create()
        view = views.CollectionsSitemap()
        collection = Collection.objects.all().first()
        assert view.items().count() == Collection.objects.all().count()
        assert view.location(collection) == '/collection/{c}/'.format(c=collection.pid)
        assert view.lastmod(collection) == collection.updated_at

    def test_export_download_zip(self):
        factory = RequestFactory()
        request = factory.get('/')
        user = UserFactory.create()
        request.user = user
        dummy_file = os.path.join(gettempdir(), 'dummy.txt')
        Path(dummy_file).touch()
        view = views.ExportDownloadZip(request=request)
        response = view.get(request, filename=dummy_file)
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200
        assert isinstance(response.serialize(), bytes)
        assert 'jekyll_site_export.zip' in str(response.serialize())

class TestVolumeSearchView(ESTestCase, TestCase):
    """View tests for Elasticsearch"""

    def setUp(self):
        """Populate tests with sample data"""
        super().setUp()
        (lang_en, _) = Language.objects.get_or_create(code="en", name="English")
        (lang_la, _) = Language.objects.get_or_create(code="la", name="Latin")
        self.volume1 = Manifest(
            pid="uniquepid1",
            label="primary",
            summary="test",
            author="Ben;An Author",
        )
        self.volume1.save()
        self.volume1.languages.add(lang_en)
        self.volume2 = Manifest(
            pid="uniquepid2",
            label="secondary",
            summary="test",
            author="Ben",
        )
        self.volume2.save()
        self.volume2.languages.add(lang_en)
        self.volume2.languages.add(lang_la)
        self.volume3 = Manifest(
            pid="uniquepid3",
            label="tertiary",
            summary="secondary",
            author="An Author",
        )
        self.volume3.save()

    def test_get_queryset(self):
        """Should be able to query by search term"""
        volume_search_view = views.VolumeSearchView()
        volume_search_view.request = Mock()
        volume_search_view.request.GET = {"q": "primary"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 1
        assert response.hits[0]['pid'] == self.volume1.pid

        # should get all volumes when request is empty
        volume_search_view.request.GET = {}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 3

        # should filter on authors
        volume_search_view.request.GET = {"author": ["Ben"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 2
        for hit in response.hits:
            assert "Ben" in hit["authors"]

        # should get all manifests matching ANY passed author
        volume_search_view.request.GET = {"author": ["Ben", "An Author"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 3

        # should get 0 for bad author
        volume_search_view.request.GET = {"author": ["Bad Author"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 0

        # should filter on languages
        volume_search_view.request.GET = {"language": ["Latin"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 1

        # should get all manifests matching ANY passed language
        volume_search_view.request.GET = {"language": ["English", "Latin"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 2


    def test_label_boost(self):
        """Should return the item matching label first, before matching summary"""
        volume_search_view = views.VolumeSearchView()
        volume_search_view.request = Mock()
        volume_search_view.request.GET = {"q": "secondary test"}
        search_results = volume_search_view.get_queryset()
        # with multiple keywords, should return all matches
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total['value'] == 3
        # should return "secondary" label match first
        assert response.hits[0]['pid'] == self.volume2.pid
