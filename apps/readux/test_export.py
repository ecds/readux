from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.views import ManifestExport, JekyllExport
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.export import IiifManifestExport, JekyllSiteExport
from iiif_prezi.loader import ManifestReader
import io
import json
import logging
import os
import re
import tempfile
import zipfile

User = get_user_model()

class ManifestExportTests(TestCase):
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

    # Things I want to test:
    # * Unzip the IIIF zip file
    #   * Verify the directory layout is correct
    #   * Open the manifest.json file
    #   * Verify that the otherContent annotation list matches the annotationlist filename
    #   * Verify that the annotationList filename matches the @id within the annotation
    # * Verify the contents of the annotationList match the OCR (or the commenting annotation)
    def test_zip_creation(self):
        zip = IiifManifestExport.get_zip(self.volume, 'v2', owners=[self.user.id])
        assert isinstance(zip, bytes)
        # unzip the file somewhere
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export-')
        iiif_zip = zipfile.ZipFile(io.BytesIO(zip), "r")
        iiif_zip.extractall(tmpdir)
        manifest_path = os.path.join(tmpdir, 'manifest.json')
        with open(manifest_path) as json_file:
            manifest = json.load(json_file)

        ocr_annotation_list_id = manifest['sequences'][0]['canvases'][0]['otherContent'][0]['@id']
        ocr_annotation_list_path = os.path.join(tmpdir, re.sub('\W','_', ocr_annotation_list_id) + ".json")
        assert os.path.exists(ocr_annotation_list_path) == 1

        with open(ocr_annotation_list_path) as json_file:
            ocr_annotation_list = json.load(json_file)
        assert ocr_annotation_list['@id'] == ocr_annotation_list_id


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

    def test_manifest_export(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('ManifestExport', kwargs=kwargs)
        request = self.factory.post(url, kwargs=kwargs)
        request.user = self.user
        response = self.manifest_export_view(request, pid=self.volume.pid, version='v2')
        assert isinstance(response.getvalue(), bytes)

    # Things I want to test:
    # * Unzip the IIIF zip file
    #   * Verify the directory layout is correct
    #   * Open the manifest.json file
    #   * Verify that the otherContent annotation list matches the annotationlist filename
    #   * Verify that the annotationList filename matches the @id within the annotation
    # * Verify the contents of the annotationList match the OCR (or the commenting annotation)


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
