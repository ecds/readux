from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.urls import reverse
from .views import ManifestDetail, ManifestSitemap, ManifestRis, ManifestExport, JekyllExport
from .models import Manifest
from ..canvases.models import Canvas
from .export import IiifManifestExport, JekyllSiteExport
from iiif_prezi.loader import ManifestReader
import json
import logging
import tempfile

class ManifestTests(TestCase):
    fixtures = ['users.json', 'kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']

    def setUp(self):
        fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
        self.user = get_user_model().objects.get(pk=1)
        self.factory = RequestFactory()
        self.client = Client()
        self.volume = Manifest.objects.get(pk='464d82f6-6ae5-4503-9afc-8e3cdd92a3f1')
        self.start_canvas = self.volume.canvas_set.filter(is_starting_page=True).first()
        self.default_start_canvas = self.volume.canvas_set.filter(is_starting_page=False).first()
        self.assumed_label = ' Descrizione del Palazzo Apostolico Vaticano '
        self.assumed_pid = 'readux:st7r6'
        self.manifest_export_view = ManifestExport.as_view()
        self.jekyll_export_view = JekyllExport.as_view()

    def test_validate_iiif(self):
        view = ManifestDetail.as_view()
        volume = Manifest.objects.all().first()
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('ManifestRender', kwargs=kwargs)
        response = self.client.get(url)
        manifest = json.loads(response.content.decode('UTF-8-sig'))
        reader = ManifestReader(response.content, version='2.1')
        try:
            mf = reader.read()
            assert mf.toJSON()
        except Exception as error:
            raise Exception(error)

        assert manifest['@id'] == "%s/manifest" % (self.volume.baseurl)
        assert manifest['label'] == self.volume.label
        assert manifest['description'] == volume.summary
        assert manifest['thumbnail']['@id'] == "%s/%s/full/600,/0/default.jpg" % (self.volume.canvas_set.all().first().IIIF_IMAGE_SERVER_BASE, self.start_canvas.pid)
        assert manifest['sequences'][0]['startCanvas'] == self.volume.start_canvas

    def test_properties(self):
        assert self.volume.publisher_bib == "In Roma : Appresso Niccol\u00f2, e Marco Pagliarini ..."
        assert self.volume.thumbnail_logo == "%s/%s/%s" % (settings.HOSTNAME, "media", "awesome.png")
        assert self.volume.baseurl == "%s/iiif/v2/%s" % (settings.HOSTNAME, self.volume.pid)
        assert self.volume.start_canvas == "%s/iiif/%s/canvas/%s" % (settings.HOSTNAME, self.volume.pid, self.start_canvas.pid)
    
    def test_default_start_canvas(self):
        self.start_canvas.is_starting_page = False
        self.start_canvas.save()
        assert self.volume.start_canvas == "%s/iiif/%s/canvas/%s" % (settings.HOSTNAME, self.volume.pid, self.default_start_canvas.pid)

    def test_meta(self):
        assert str(self.volume) == self.assumed_label

    def test_sitemap(self):
        sm = ManifestSitemap()
        assert len(sm.items()) == Manifest.objects.all().count()
        assert sm.location(self.volume) == "/iiif/v2/%s/manifest" % (self.assumed_pid)

    def test_ris_view(self):
        ris = ManifestRis()
        assert ris.get_context_data(volume=self.assumed_pid)['volume'] == self.volume

    def test_zip_creation(self):
        zip = IiifManifestExport.get_zip(self.volume, 'v2', owners=[self.user.id])
        assert isinstance(zip, bytes)

    def test_jekyll_site_export(self):
        j = JekyllSiteExport(self.volume, 'v2', owners=[self.user.id])
        zip = j.get_zip()
        tempdir = j.generate_website()
        web_zip = j.website_zip()
        # j.import_iiif_jekyll(j.manifest, j.jekyll_site_dir)
        assert isinstance(zip, tempfile._TemporaryFileWrapper)
        assert "%s_annotated_site_" % (str(self.volume.pk)) in zip.name
        assert zip.name.endswith('.zip')
        assert isinstance(web_zip, tempfile._TemporaryFileWrapper)
        assert "%s_annotated_site_" % (str(self.volume.pk)) in web_zip.name
        assert web_zip.name.endswith('.zip')
        assert 'tmp-rdx-export' in tempdir
        assert tempdir.endswith('/export')

    def test_maifest_export(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('ManifestExport', kwargs=kwargs)
        request = self.factory.post(url, kwargs=kwargs)
        request.user = self.user
        response = self.manifest_export_view(request, pid=self.volume.pid, version='v2')
        assert isinstance(response.getvalue(), bytes)

    def test_jekyll_export_exclude_download(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('JekyllExport', kwargs=kwargs)
        kwargs['deep_zoom'] = 'exclude'
        kwargs['mode'] = 'download'
        request = self.factory.post(url, data=kwargs) 
        request.user = self.user       
        response = self.jekyll_export_view(request, pid=self.volume.pid, version='v2', content_type="application/x-www-form-urlencoded")
        assert isinstance(response.getvalue(), bytes)

    def test_jekyll_export_include_download(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('JekyllExport', kwargs=kwargs)
        kwargs['deep_zoom'] = 'include'
        kwargs['mode'] = 'download'
        request = self.factory.post(url, data=kwargs) 
        request.user = self.user       
        response = self.jekyll_export_view(request, pid=self.volume.pid, version='v2', content_type="application/x-www-form-urlencoded")
        assert isinstance(response.getvalue(), bytes)
