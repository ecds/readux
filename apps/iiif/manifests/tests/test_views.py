'''
'''
import json
from datetime import datetime
from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.serializers import serialize
from allauth.socialaccount.models import SocialAccount

from ..admin import ManifestAdmin
from ..views import AddToCollectionsView, ManifestSitemap, ManifestRis
from ..models import Manifest
from ..forms import ManifestsCollectionsForm
from .factories import ManifestFactory, EmptyManifestFactory
from ...canvases.models import Canvas
from ...canvases.tests.factories import CanvasFactory
from ...kollections.models import Collection
from ...kollections.tests.factories import CollectionFactory

USER = get_user_model()

class ManifestTests(TestCase):
    fixtures = [
        'users.json',
        'kollections.json',
        'manifests.json',
        'canvases.json',
        'annotations.json'
    ]

    def setUp(self):
        self.user = get_user_model().objects.get(pk=111)
        self.factory = RequestFactory()
        self.client = Client()
        self.volume = ManifestFactory.create(
            publisher='ECDS',
            published_city='Atlanta'
        )
        for num in range(0, 3):
            CanvasFactory.create(
                manifest=self.volume,
                position=num
            )
        self.start_canvas = self.volume.canvas_set.filter(manifest=self.volume).first()
        self.default_start_canvas = self.volume.canvas_set.filter(is_starting_page=False).first()
        self.assumed_label = ' Descrizione del Palazzo Apostolico Vaticano '
        self.assumed_pid = self.volume.pid
        self.volume.save()

    def test_properties(self):
        assert self.volume.publisher_bib == 'Atlanta : ECDS'
        assert self.volume.thumbnail_logo.endswith("/media/logos/ecds.png")
        assert self.volume.baseurl.endswith("/iiif/v2/%s" % (self.volume.pid))
        assert self.volume.start_canvas.identifier.endswith("/iiif/%s/canvas/%s" % (self.volume.pid, self.volume.start_canvas.pid))

    def test_default_start_canvas(self):
        self.start_canvas.is_starting_page = False
        self.start_canvas.save()
        self.volume.start_canvas = None
        self.volume.save()
        self.volume.refresh_from_db()
        assert self.volume.start_canvas.identifier.endswith("/iiif/%s/canvas/%s" % (self.volume.pid, self.default_start_canvas.pid))

    def test_meta(self):
        assert str(self.volume) == self.volume.label

    def test_sitemap(self):
        site_map = ManifestSitemap()
        assert len(site_map.items()) == Manifest.objects.all().count()
        assert site_map.location(self.volume) == "/iiif/v2/%s/manifest" % (self.volume.pid)

    def test_ris_view(self):
        ris = ManifestRis()
        assert ris.get_context_data(volume=self.assumed_pid)['volume'] == self.volume

    def test_plain_export_view(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('PlainExport', kwargs=kwargs)
        response = self.client.get(url)
        assert response.status_code == 200

    def test_autocomplete_label(self):
        assert Manifest.objects.all().first().autocomplete_label() == Manifest.objects.all().first().label

    def test_absolute_url(self):
        assert Manifest.objects.all().first().get_absolute_url() == "%s/volume/%s" % (settings.HOSTNAME, Manifest.objects.all().first().pid)

    # def test_manifest_search_vector_exists(self):
    #     volume = ManifestFactory.create()
    #     assert not self.volume.search_vector
    #     volume.save()
    #     volume.refresh_from_db()
    #     assert volume.search_vector is not  None

    def test_multiple_starting_canvases(self):
        volume = EmptyManifestFactory.create(canvas=None)
        assert volume.canvas_set.exists() is False
        for index, _ in enumerate(range(4)):
            CanvasFactory.create(manifest=volume, is_starting_page=True, position=index+1)
        manifest = json.loads(
            serialize(
                'manifest',
                [volume],
                version='v2',
                annotators='Tom',
                exportdate=datetime.utcnow()
            )
        )
        first_canvas = volume.canvas_set.all().first()
        assert volume.start_canvas.position <= 1
        assert first_canvas.position <= 1
        assert first_canvas.pid in manifest['thumbnail']['@id']

    def test_no_starting_canvases(self):
        manifest = ManifestFactory.create()
        try:
            manifest.canvas_set.all().get(is_starting_page=True)
        except Canvas.DoesNotExist as error:
            assert str(error) == 'Canvas matching query does not exist.'
        serialized_manifest = json.loads(
            serialize(
                'manifest',
                [manifest]
            )
        )
        assert manifest.canvas_set.all().first().pid in serialized_manifest['thumbnail']['@id']

    # TODO: Test with 0 manifests, 1 manifests, non-manifest obj
    def test_add_to_collections_view_context(self):
        """it should add the passed manifests to view context"""
        manifest1 = ManifestFactory.create()
        manifest2 = ManifestFactory.create()
        ids = ','.join([str(manifest1.pk), str(manifest2.pk)])
        request = self.factory.get(
            reverse('admin:manifests_manifest_changelist') + 'add_to_collections/?ids=' + ids
        )
        request.user = self.user
        view = AddToCollectionsView()
        model_admin = ManifestAdmin(model=Manifest, admin_site=AdminSite())
        view.setup(request, model_admin=model_admin)

        context = view.get_context_data()
        self.assertIn('manifests', context)
        self.assertIn(manifest1, context['manifests'])
        self.assertIn(manifest2, context['manifests'])

    def test_add_to_collections_view_function(self):
        """it should add the passed manifests to the selected collections"""
        manifest1 = ManifestFactory.create()
        manifest2 = ManifestFactory.create()
        collection1 = CollectionFactory.create()
        collection2 = CollectionFactory.create()
        ids = ','.join([str(manifest1.pk), str(manifest2.pk)])
        request = self.factory.get(
            reverse('admin:manifests_manifest_changelist') + 'add_to_collections/?ids=' + ids
        )
        request.user = self.user
        view = AddToCollectionsView()
        model_admin = ManifestAdmin(model=Manifest, admin_site=AdminSite())
        view.setup(request, model_admin=model_admin)
        qs = Collection.objects.filter(pk__in=[collection1.pk, collection2.pk])
        form = ManifestsCollectionsForm(data={"collections": qs})

        assert len(manifest1.collections.all()) == 0
        assert len(manifest2.collections.all()) == 0
        view.add_manifests_to_collections(form)
        assert len(manifest1.collections.all()) == 2
        assert len(manifest2.collections.all()) == 2
