from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .views import ManifestsForCollection
from .models import Collection
import config.settings.local as settings
from os import path
import json

class KollectionTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
    
    def setUp(self):
        self.client = Client()
        self.collection = Collection.objects.all().first()
        self.volume = self.collection.manifests.all()[0]

    def test_collection_serialization(self):
        kwargs = { 'pid': Collection.objects.all().first().pid, 'version': 'v2' }
        url = reverse('CollectionRender', kwargs=kwargs)
        response = self.client.get(url)
        collection = json.loads(response.content.decode('UTF-8-sig'))
        assert collection['@type'] == 'sc:Collection'
        assert collection['@id'] == "%s/iiif/v2/%s/collection" % (settings.HOSTNAME, self.collection.pid)
        assert len(collection['manifests']) == self.collection.manifests.all().count()
        assert collection['label'] == self.collection.label
        assert collection['description'] == self.collection.summary
        assert collection['manifests'][0]['@id'] == "%s/iiif/%s/manifest" % (settings.HOSTNAME, self.volume.pid)
        assert collection['manifests'][0]['@type'] == 'sc:Manifest'
        assert collection['manifests'][0]['label'] == self.volume.label
    
    def test_collection_manifest_list(self):
        kwargs = { 'pid': Collection.objects.all().first().pid, 'version': 'v2' }
        url = reverse('CollectionManifestRender', kwargs=kwargs)
        response = self.client.get(url)
        collection = json.loads(response.content.decode('UTF-8-sig'))
        assert len(collection) == self.collection.manifests.all().count()
        assert collection[0]['@id'] == "%s/iiif/%s/manifest" % (settings.HOSTNAME, self.volume.pid)
        assert collection[0]['@type'] == 'sc:Manifest'
        assert collection[0]['label'] == self.volume.label
    
    def test_collection_images(self):
        image_path = 'apps/iiif/kollections/fixtures/rome.jpg'
        self.collection.original = SimpleUploadedFile(name='rome.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')
        self.collection.save()
        # NOTE pytest uses some arbitrary tmp file naming structure.
        assert self.collection.original.path.split('/')[-1] == 'rome.jpg'
        # assert self.collection.upload.path.split('/')[-1] == 'rome.jpg'
        assert self.collection.header.path.split('/')[-1] == 'rome_header.jpg'
        assert self.collection.thumbnail.path.split('/')[-1] == 'rome_thumb.jpg'
        assert self.collection.original.url == "%soriginals/rome.jpg" % (settings.MEDIA_URL)
        # assert self.collection.upload.url == "%s/uploads/rome.jpg" % (settings.MEDIA_URL)
        assert self.collection.header.url == "%sheaders/rome_header.jpg" % (settings.MEDIA_URL)
        assert self.collection.thumbnail.url == "%sthumbnails/rome_thumb.jpg" % (settings.MEDIA_URL)
        assert path.isfile(self.collection.original.path)
        # assert path.isfile(self.collection.upload.path)
        assert path.isfile(self.collection.header.path)
        assert path.isfile(self.collection.thumbnail.path)
