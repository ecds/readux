"""
Test class for Elasticsearch indexing.
"""

from django.test import TestCase
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.documents import ManifestDocument
from apps.iiif.manifests.tests.factories import ManifestFactory

class ManifestDocumentTest(TestCase):
    """Tests for IIIF manifest indexing"""
    def setUp(self):
        self.doc = ManifestDocument()

    def test_prepare_authors(self):
        """Test authors returned as array instead of string"""
        # test no author
        manifest = ManifestFactory.create()
        assert self.doc.prepare_authors(instance=manifest) == []
        # test empty string
        manifest.author = ""
        assert self.doc.prepare_authors(instance=manifest) == []
        # test no semicolon
        manifest.author = "test author"
        assert self.doc.prepare_authors(instance=manifest) == ["test author"]
        # test semicolon separation
        manifest.author = "test author;example author;ben"
        assert self.doc.prepare_authors(instance=manifest) == [
            "test author", "example author", "ben"
        ]
        # test whitespace stripping
        manifest.author = "test author; example author; ben"
        assert self.doc.prepare_authors(instance=manifest) == [
            "test author", "example author", "ben"
        ]

    def test_prepare_has_pdf(self):
        """Test PDF presence detected accurately"""
        # test no pdf
        manifest = ManifestFactory.create()
        assert not self.doc.prepare_has_pdf(instance=manifest)
        # test empty string
        manifest.pdf = ""
        assert not self.doc.prepare_has_pdf(instance=manifest)
        # test with pdf
        manifest.pdf = "url"
        assert self.doc.prepare_has_pdf(instance=manifest)

    def test_get_queryset(self):
        """Test prefetching"""
        manifest = ManifestFactory.create()
        # connect a collection and manifest
        collection = Collection(label="test collection")
        collection.save()
        manifest.collections.add(collection)
        # get prefetched objects cache for elastic queryset
        qs_manifest = self.doc.get_queryset().first()
        prefetched = qs_manifest._prefetched_objects_cache # pylint: disable=protected-access
        # should be a dict of prefetched relations
        assert isinstance(prefetched, dict)
        # should have one collection, which is the above collection
        assert prefetched['collections'].count() == 1
        assert prefetched['collections'].first().pk == collection.pk
