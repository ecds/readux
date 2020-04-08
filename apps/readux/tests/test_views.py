import pytest
from django.test import RequestFactory
from apps.readux.views import PageDetail, ManifestsSitemap, CollectionsSitemap
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.iiif.kollections.tests.factories import CollectionFactory
from apps.iiif.kollections.models import Collection
from apps.iiif.canvases.models import Canvas
from wagtail.core.models import Page
from apps.users.tests.factories import UserFactory
import config.settings.local as settings

pytestmark = pytest.mark.django_db

class TestReaduxViews:
    
    def test_page_detail_context(self):
        factory = RequestFactory()
        user = UserFactory.create()
        assert not user._state.adding
        volume = ManifestFactory.create()
        # kwargs = {'volume': volume.pid, 'page': volume.canvas_set.all().first().pid}
        # url = reverse('page', kwargs=kwargs)
        request = factory.get('/')
        # request.kwargs = kwargs
        request.user = user
        view = PageDetail(request=request)
        data = view.get_context_data(volume=volume.pid, page=volume.canvas_set.all().first().pid)
        assert data['volume'].pid == volume.pid
        assert isinstance(data['volume'], Manifest)
        assert isinstance(data['page'], Canvas)
        # assert isinstance(data['collectionlink'], Page)
        assert isinstance(data['user_annotation_page_count'], int)
        assert isinstance(data['user_annotation_count'], int)
        assert data['mirador_url'] == settings.MIRADOR_URL

    def test_manifests_sitemap(self):
        for n in range(5):
            ManifestFactory.create()
        view = ManifestsSitemap()
        manifest = Manifest.objects.all().first()
        assert view.items().count() == Manifest.objects.all().count()
        assert view.location(manifest) == '/volume/{m}/page/all'.format(m=manifest.pid)
        assert view.lastmod(manifest) == manifest.updated_at

    def test_collections_sitemap(self):
        for n in range(3):
            CollectionFactory.create()
        view = CollectionsSitemap()
        collection = Collection.objects.all().first()
        assert view.items().count() == Collection.objects.all().count()
        assert view.location(collection) == '/collection/{c}/'.format(c=collection.pid)
        assert view.lastmod(collection) == collection.updated_at
