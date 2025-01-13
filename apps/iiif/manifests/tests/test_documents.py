"""
Test class for Elasticsearch indexing.
"""

import random
import string
from django.test import TestCase
from django_elasticsearch_dsl.test import ESTestCase
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.documents import ManifestDocument
from apps.iiif.manifests.models import Language, Manifest
from apps.iiif.manifests.tests.factories import ManifestFactory


class ManifestDocumentTest(ESTestCase, TestCase):
    """Tests for IIIF manifest indexing"""

    def setUp(self):
        super().setUp()
        self.doc = ManifestDocument()
        (self.lang_en, _) = Language.objects.get_or_create(code="en", name="English")
        (self.lang_la, _) = Language.objects.get_or_create(code="la", name="Latin")

    def test_prepare_authors(self):
        """Test authors returned as array instead of string"""
        # test no author
        manifest = ManifestFactory.create()
        assert self.doc.prepare_authors(instance=manifest) == ["[no author]"]
        # test empty string
        manifest.author = ""
        assert self.doc.prepare_authors(instance=manifest) == ["[no author]"]
        # test no semicolon
        manifest.author = "test author"
        assert self.doc.prepare_authors(instance=manifest) == ["test author"]
        # test semicolon separation
        manifest.author = "test author;example author;ben"
        assert self.doc.prepare_authors(instance=manifest) == [
            "test author",
            "example author",
            "ben",
        ]
        # test whitespace stripping
        manifest.author = "test author; example author; ben"
        assert self.doc.prepare_authors(instance=manifest) == [
            "test author",
            "example author",
            "ben",
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

    def test_prepare_label_alphabetical(self):
        """Should strip accents from text"""
        manifest = ManifestFactory.create(label="éclair")
        assert self.doc.prepare_label_alphabetical(instance=manifest) == "eclair"
        # should only return the first 64 characters
        random_100_chars = "".join(random.choices(string.ascii_letters, k=100))
        manifest.label = random_100_chars
        label_alphabetical = self.doc.prepare_label_alphabetical(instance=manifest)
        assert label_alphabetical == random_100_chars[0:64]
        assert len(label_alphabetical) == 64
        # should return "[no label]" for no label
        manifest.label = ""
        assert self.doc.prepare_label_alphabetical(instance=manifest) == "[no label]"
        manifest.label = None
        assert self.doc.prepare_label_alphabetical(instance=manifest) == "[no label]"

    def test_prepare_languages(self):
        """Test languages converted into string array"""
        # test no languages
        manifest = ManifestFactory.create()
        assert self.doc.prepare_languages(instance=manifest) == ["[no language]"]
        # test one language
        manifest.languages.add(self.lang_en)
        assert self.doc.prepare_languages(instance=manifest) == ["English"]
        # test multiple languages
        manifest.languages.add(self.lang_la)
        assert len(self.doc.prepare_languages(instance=manifest)) == 2

    def test_prepare_summary(self):
        """Test summary stripped of HTML tags"""
        manifest = ManifestFactory.create(summary="No html tags")
        assert self.doc.prepare_summary(instance=manifest) == manifest.summary
        manifest.summary = "<p><strong>Has</strong> HTML tags</p>"
        assert self.doc.prepare_summary(instance=manifest) == "Has HTML tags"

    def test_get_queryset(self):
        """Test prefetching"""
        manifest = ManifestFactory.create()
        # connect a collection and manifest
        collection = Collection(label="test collection")
        collection.save()
        manifest.collections.add(collection)
        # get prefetched objects cache for elastic queryset
        qs_manifest = self.doc.get_queryset().first()
        prefetched = (
            qs_manifest._prefetched_objects_cache
        )  # pylint: disable=protected-access
        # should be a dict of prefetched relations
        assert isinstance(prefetched, dict)
        # should have one collection, which is the above collection
        assert prefetched["collections"].count() == 1
        assert prefetched["collections"].first().pk == collection.pk

    def test_exclude_searchable_false(self):
        """Do not index objects when searchable is False."""
        searchable_manifest = ManifestFactory.create()
        excluded_manifest = ManifestFactory.create(searchable=False)
        self.doc.update(searchable_manifest)
        self.doc.update(excluded_manifest)
        response = self.doc.search()
        results = response.to_queryset()
        assert searchable_manifest.pid in [m.pid for m in results]
        assert excluded_manifest.pid not in [m.pid for m in results]

    def test_remove_manifest_from_index_searchable_false(self):
        """A manifest should be removed when searchable changes to false"""
        searchable_manifest = ManifestFactory.create()
        manifest = ManifestFactory.create()
        self.doc.update(manifest)
        self.doc.update(searchable_manifest)
        response = self.doc.search()
        results = response.to_queryset()
        assert manifest.pid in [m.pid for m in results]
        manifest.searchable = False
        manifest.save()
        manifest.refresh_from_db()
        response = self.doc.search()
        results = response.to_queryset()
        assert manifest.pid not in [m.pid for m in results]

    # Removed test because we don't want to trigger a reindex when a collection is saved.
    # def test_get_instances_from_related(self):
    #     """Should get manifests from related collections"""
    #     manifest = ManifestFactory.create()
    #     # connect a collection and manifest
    #     collection = Collection(label="test collection")
    #     collection.save()
    #     manifest.collections.add(collection)
    #     instances = self.doc.get_instances_from_related(related_instance=collection)
    #     # should get the manifest related to this collection
    #     self.assertQuerysetEqual(instances, [manifest])
