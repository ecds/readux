import os
import pytest
from tempfile import gettempdir
from pathlib import Path
from django.test import RequestFactory
from django.http import HttpResponse
from apps.readux import views
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.iiif.kollections.tests.factories import CollectionFactory
from apps.iiif.kollections.models import Collection
from apps.iiif.canvases.models import Canvas
from apps.users.tests.factories import UserFactory
import config.settings.local as settings

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
