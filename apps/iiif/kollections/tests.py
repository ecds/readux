from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers import serialize
from .views import ManifestsForCollection, CollectionSitemap
from .models import Collection
from ..manifests.models import Manifest
import config.settings.local as settings
from os import path
from PIL import Image
import json

class KollectionTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
    
    def setUp(self):
        self.client = Client()
        self.collection = Collection.objects.all().first()
        self.volume = self.collection.manifests.all().first()
        self.fixture_path = 'apps/iiif/kollections/fixtures/'

    def test_collection_serialization(self):
        kwargs = { 'pid': self.collection.pid, 'version': 'v2' }
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
        kwargs = { 'pid': self.collection.pid, 'version': 'v2' }
        url = reverse('CollectionManifestRender', kwargs=kwargs)
        response = self.client.get(url)
        collection = json.loads(response.content.decode('UTF-8-sig'))
        assert len(collection) == self.collection.manifests.all().count()
        assert collection[0]['@id'] == "%s/iiif/%s/manifest" % (settings.HOSTNAME, self.volume.pid)
        assert collection[0]['@type'] == 'sc:Manifest'
        assert collection[0]['label'] == self.volume.label
    
    def test_collection_images(self):
        image_path = "{p}test_vert.jpg".format(p=self.fixture_path)
        self.collection.original = SimpleUploadedFile(name='test_vert.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')
        self.collection.save()
        # NOTE pytest uses some arbitrary tmp file naming structure.
        assert self.collection.original.path.split('/')[-1] == 'test_vert.jpg'
        # assert self.collection.upload.path.split('/')[-1] == 'test_vert.jpg'
        assert self.collection.header.path.split('/')[-1] == 'test_vert_header.jpg'
        assert self.collection.thumbnail.path.split('/')[-1] == 'test_vert_thumb.jpg'
        assert self.collection.original.url == "%soriginals/test_vert.jpg" % (settings.MEDIA_URL)
        # assert self.collection.upload.url == "%s/uploads/test_vert.jpg" % (settings.MEDIA_URL)
        assert self.collection.header.url == "%sheaders/test_vert_header.jpg" % (settings.MEDIA_URL)
        assert self.collection.thumbnail.url == "%sthumbnails/test_vert_thumb.jpg" % (settings.MEDIA_URL)
        assert path.isfile(self.collection.original.path)
        # assert path.isfile(self.collection.upload.path)
        assert path.isfile(self.collection.header.path)
        assert path.isfile(self.collection.thumbnail.path)
    
    def test_autocomplete_label(self):
        assert self.collection.autocomplete_label() == self.collection.label
    
    def test_string(self):
        assert str(self.collection) == self.collection.label

    def test_invalid_image_file_types(self):
        collection = Collection()
        collection.label = 'Some Lousy Collection'
        invalid_test_images = {
            'tiff': "{p}test.tiff".format(p=self.fixture_path),
            'jp2': "{p}test.jp2".format(p=self.fixture_path)
        }
        for file_type, file_path in invalid_test_images.items() :
            collection.original = SimpleUploadedFile(name="test.{t}".format(t=file_type), content=open(file_path, 'rb').read())
            try:
                collection.save()
            except Exception as error:
                assert str(error) == 'Could not create thumbnail - is the file type valid?'
    
    def test_valid_image_file_types(self):
        collection = Collection()
        collection.label = 'Some Lousy Collection'
        invalid_test_images = {
            'png': "{p}test.tiff".format(p=self.fixture_path),
            'gif': "{p}test.gif".format(p=self.fixture_path),
            'jpeg': "{p}test.jpeg".format(p=self.fixture_path)
        }
        for file_type, file_path in invalid_test_images.items():
            collection.original = SimpleUploadedFile(name="test.{t}".format(t=file_type), content=open(file_path, 'rb').read())
            collection.save()
            assert collection.thumbnail.url == "{p}thumbnails/test_thumb.{t}".format(p=settings.MEDIA_URL, t=file_type)
            
    def test_thumbnail_size(self):
        collection = Collection()
        images = {
            'test_horz.jpg': "{p}test_horz.jpg".format(p=self.fixture_path),
            'test_vert.jpg': "{p}test_vert.jpg".format(p=self.fixture_path),
            'test_square.png': "{p}test_square.png".format(p=self.fixture_path),
            'test_400x500.png': "{p}test_400x500.png".format(p=self.fixture_path)
        }
        for file_name, file_path in images.items():
            collection.original = SimpleUploadedFile(name=file_name, content=open(file_path, 'rb').read())
            collection.save()
            thumbnail = Image.open(collection.thumbnail.path)
            assert thumbnail.size == (400, 500)
    
    def test_sitemap(self):
        assert len(CollectionSitemap().items()) == Collection.objects.all().count()
        for collection in CollectionSitemap().items():
            assert collection in Collection.objects.all()
        assert CollectionSitemap().location(self.collection) == "/iiif/v2/{c}/collection".format(c=self.collection.pid)
    
    def test_manifest_for_collection_serializer(self):
        manifest = json.loads(serialize('collection_manifest', Manifest.objects.all(), is_list = True))
        assert manifest[0]['@type'] == 'sc:Manifest'
        assert isinstance(manifest, list)
    

    def test_serialize_list_of_collections(self):
        collection = json.loads(serialize('kollection', Collection.objects.all(), is_list = True))
        assert collection[0]['@type'] == 'sc:Collection'
        assert isinstance(collection, list)

    def test_serialize_single_object(self):
        collection = json.loads(serialize('kollection', [Collection.objects.all().first()]))
        assert collection['@type'] == 'sc:Collection'
        assert isinstance(collection, dict)
