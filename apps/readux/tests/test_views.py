"""Test for readux views"""

import os
from unittest.mock import Mock, patch
from tempfile import gettempdir
from pathlib import Path
import pytest
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django_elasticsearch_dsl.test import ESTestCase
from apps.readux import views
from apps.iiif.manifests.models import Language, Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.iiif.manifests.documents import ManifestDocument
from apps.iiif.kollections.tests.factories import CollectionFactory
from apps.iiif.kollections.models import Collection
from apps.iiif.canvases.models import Canvas
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestReaduxViews:
    """
    Test views for readux app
    """

    def test_page_detail_context(self):
        """Test"""
        factory = RequestFactory()
        user = UserFactory.create()
        assert not user._state.adding
        volume = ManifestFactory.create()
        request = factory.get("/")
        request.user = user
        view = views.PageDetail(request=request)
        data = view.get_context_data(
            volume=volume.pid, page=volume.canvas_set.all().first().pid
        )
        assert data["volume"].pid == volume.pid
        assert isinstance(data["volume"], Manifest)
        assert isinstance(data["page"], Canvas)
        assert isinstance(data["user_annotation_page_count"], int)
        assert isinstance(data["user_annotation_count"], int)

    def test_page_detail_context_with_no_page_in_kwargs(self):
        """Test"""
        factory = RequestFactory()
        request = factory.get("/")
        user = UserFactory.create()
        request.user = user
        volume = ManifestFactory.create()
        view = views.PageDetail(request=request)
        data = view.get_context_data(volume=volume.pid)
        assert data["volume"].pid == volume.pid
        assert data["page"].pid == volume.canvas_set.all().first().pid

    def test_manifests_sitemap(self):
        """Test"""
        for _ in range(5):
            ManifestFactory.create()
        view = views.ManifestsSitemap()
        manifest = Manifest.objects.all().first()
        assert view.items().count() == Manifest.objects.all().count()
        assert view.location(manifest) == f"/volume/{manifest.pid}/page/all"
        assert view.lastmod(manifest) == manifest.updated_at

    def test_collections_sitemap(self):
        """Test"""
        for n in range(3):
            CollectionFactory.create()
        view = views.CollectionsSitemap()
        collection = Collection.objects.all().first()
        assert view.items().count() == Collection.objects.all().count()
        assert view.location(collection) == f"/collection/{collection.pid}/"
        assert view.lastmod(collection) == collection.updated_at

    def test_export_download_zip(self):
        """Test"""
        factory = RequestFactory()
        request = factory.get("/")
        user = UserFactory.create()
        request.user = user
        dummy_file = os.path.join(gettempdir(), "dummy.txt")
        Path(dummy_file).touch()
        view = views.ExportDownloadZip(request=request)
        response = view.get(request, filename=dummy_file)
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200
        assert isinstance(response.serialize(), bytes)
        assert "jekyll_site_export.zip" in str(response.serialize())


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
            published_date_edtf="2022-04-14",
        )
        self.volume1.save()
        self.volume1.languages.add(lang_en)
        self.volume2 = Manifest(
            pid="uniquepid2",
            label="secondary",
            summary="test",
            author="Ben",
            published_date_edtf="2022-11-23",
        )
        self.volume2.save()
        self.volume2.languages.add(lang_en)
        self.volume2.languages.add(lang_la)
        self.volume3 = Manifest(
            pid="uniquepid3",
            label="tertiary",
            summary="secondary",
            author="An Author",
            published_date_edtf="1900/1909",
        )
        self.volume3.save()

        collection = Collection(label="test collection")
        collection.save()
        self.volume1.collections.add(collection)
        self.volume3.collections.add(collection)

        for manifest in Manifest.objects.all():
            ManifestDocument().update(manifest, True, "index")

    def test_get_queryset(self):
        """Should be able to query by search term"""
        volume_search_view = views.VolumeSearchView()
        volume_search_view.request = Mock()
        volume_search_view.request.GET = {"q": "primary"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 1
        assert response.hits[0]["pid"] == self.volume1.pid

        # should get all volumes when request is empty
        volume_search_view.request.GET = {}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 3
        # should sort by label alphabetically by default
        assert response.hits[0]["label"] == self.volume1.label

    def test_get_queryset_filters(self):
        """Should filter according to chosen filters"""

        # Reindex each volume
        index = ManifestDocument()
        for manifest in Manifest.objects.all():
            index.update(manifest, True, "index")

        volume_search_view = views.VolumeSearchView()
        volume_search_view.request = Mock()

        # should filter on authors
        volume_search_view.request.GET = {"author": ["Ben"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 2
        for hit in response.hits:
            assert "Ben" in hit["authors"]

        # should get all manifests matching ANY passed author
        volume_search_view.request.GET = {"author": ["Ben", "An Author"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 3

        # should get 0 for bad author
        volume_search_view.request.GET = {"author": ["Bad Author"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 0

        # should filter on languages
        volume_search_view.request.GET = {"language": ["Latin"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 1

        # should get all manifests matching ANY passed language
        volume_search_view.request.GET = {"language": ["English", "Latin"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 2

        # should filter on collections label
        volume_search_view.request.GET = {"collection": ["test collection"]}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 2

        # should filter on start and end date
        volume_search_view.request.GET = {
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
        }
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 2

        # should filter on start and end date (fuzzy)
        volume_search_view.request.GET = {
            "start_date": "1899-01-01",
            "end_date": "1910-01-01",
        }
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 1

    def test_get_queryset_sorting(self):
        """Should sort according to default or chosen sort"""
        volume_search_view = views.VolumeSearchView()
        volume_search_view.request = Mock()

        # should sort by label alphabetically when sort is specified but empty:
        volume_search_view.request.GET = {"sort": ""}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["label"] == self.volume1.label

        # should sort by label, in reverse alphabetical order
        volume_search_view.request.GET = {"sort": "-label_alphabetical"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["label"] == self.volume3.label

        # should sort by relevance
        volume_search_view.request.GET = {"q": "test", "sort": "_score"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["pid"] != self.volume3.pid

        # should sort by relevance
        volume_search_view.request.GET = {"q": "test", "sort": ""}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["pid"] != self.volume3.pid

        # should sort by date added (asc)
        volume_search_view.request.GET = {"sort": "created_at"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["pid"] == self.volume1.pid

        # should sort by date added (desc)
        volume_search_view.request.GET = {"sort": "-created_at"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["pid"] == self.volume3.pid

        # should sort by date published (asc)
        volume_search_view.request.GET = {"sort": "date_sort_ascending"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["pid"] == self.volume3.pid

        # should sort by date published (desc)
        volume_search_view.request.GET = {"sort": "-date_sort_descending"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert response.hits[0]["pid"] == self.volume2.pid

    def test_label_boost(self):
        """Should return the item matching label first, before matching summary"""
        volume_search_view = views.VolumeSearchView()
        volume_search_view.request = Mock()
        volume_search_view.request.GET = {"q": "secondary test"}
        search_results = volume_search_view.get_queryset()
        # with multiple keywords, should return all matches
        response = search_results.execute(ignore_cache=True)
        assert response.hits.total["value"] == 3
        # should return "secondary" label match first (sort by relevance is default)
        assert response.hits[0]["pid"] == self.volume2.pid

    def test_highlighting(self):
        """Should highlight text matching query"""
        volume_search_view = views.VolumeSearchView()
        volume_search_view.request = Mock()
        volume_search_view.request.GET = {"q": "secondary"}
        search_results = volume_search_view.get_queryset()
        response = search_results.execute(ignore_cache=True)
        assert "<em>secondary</em>" in response.hits[0].meta.highlight.label[0]

    @patch("apps.readux.forms.ManifestSearchForm.set_facets")
    @patch("apps.readux.forms.ManifestSearchForm.set_date")
    def test_get_context_data(self, mock_set_date, mock_set_facets):
        """Should call form's set_facets method on returned facets from Elasticsearch"""
        volume_search_view = views.VolumeSearchView(kwargs={})
        volume_search_view.request = Mock()
        volume_search_view.request.GET = {}
        volume_search_view.facets = [
            ("language", Mock()),
            ("author", Mock()),
            ("collections", Mock()),
        ]
        with patch("apps.readux.views.VolumeSearchView.get_queryset") as mock_queryset:
            volume_search_view.queryset = mock_queryset
            volume_search_view.object_list = mock_queryset
            mock_queryset.return_value.execute.return_value = Mock()
            response = mock_queryset.return_value.execute.return_value

            # these are not nested facets, so delete "inner" attributes
            del response.aggregations.language.inner
            del response.aggregations.author.inner

            volume_search_view.get_context_data()
            mock_set_facets.assert_called_with(
                {
                    "language": response.aggregations.language.buckets,
                    "author": response.aggregations.author.buckets,
                    # collections IS nested, so it should have "inner" attribute
                    "collections": response.aggregations.collections.inner.buckets,
                }
            )

            # should call set_date with the aggregated min and max dates (as strings)
            mock_set_date.assert_called_with(
                response.aggregations.min_date.value_as_string,
                response.aggregations.max_date.value_as_string,
            )
