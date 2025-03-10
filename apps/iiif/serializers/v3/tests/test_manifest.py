"""Test Module for IIIF Serializers"""

import json
from random import randint
from django.test import TestCase
from django.core.serializers import serialize, deserialize
from django.contrib.auth import get_user_model
from apps.iiif.annotations.tests.factories import AnnotationFactory
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.kollections.tests.factories import CollectionFactory
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.iiif.manifests.models import Language
from apps.readux.tests.factories import UserAnnotationFactory
from apps.users.tests.factories import UserFactory
from .complex_metadata import complex_metadata

User = get_user_model()


class SerializerTests(TestCase):
    def setUp(self):
        """_summary_"""
        self.manifest = ManifestFactory.create()
        self.user = UserFactory.create()
        for _ in range(0, 10):
            canvas = CanvasFactory.create(manifest=self.manifest)
            for _ in range(0, randint(3, 5)):
                AnnotationFactory.create(canvas=canvas)
            for _ in range(0, randint(3, 5)):
                UserAnnotationFactory.create(canvas=canvas, owner=self.user)
        for _ in range(0, 2):
            self.manifest.collections.add(CollectionFactory.create())
        self.manifest.languages.add(Language.objects.get(code="en"))

        self.manifest.refresh_from_db()

        self.serialized_manifest = json.loads(
            serialize("manifest_v3", [self.manifest], current_user=self.user)
        )

    def test_manifest(self):
        """It should serialize a volume with the correct number of canvases."""
        assert (
            len(self.serialized_manifest["items"]) == self.manifest.canvas_set.count()
        )

    def test_deserializer(self):
        """It should deserialize an manifest."""
        manifest, relations = deserialize("manifest_v3", self.serialized_manifest)
        assert manifest["pid"] == self.manifest.pid
        assert len(relations["languages"]) == 1
        assert len(relations["collections"]) == 2

    def test_serializing_complex_metadata(self):
        """It should serialize extra metadata"""
        self.manifest.metadata = complex_metadata()
        self.manifest.save()
        self.manifest.refresh_from_db()
        updated_serialized_manifest = json.loads(
            serialize("manifest_v3", [self.manifest], current_user=self.user)
        )
        for item in complex_metadata():
            assert item in updated_serialized_manifest["metadata"]
        assert "Collections" in [
            md["label"] for md in updated_serialized_manifest["metadata"]
        ]

    def test_deserializing_complex_metadata(self):
        """It should serialize extra metadata"""
        self.manifest.metadata = complex_metadata()
        self.manifest.save()
        self.manifest.refresh_from_db()
        updated_serialized_manifest = json.loads(
            serialize("manifest_v3", [self.manifest], current_user=self.user)
        )
        manifest, relations = deserialize("manifest_v3", updated_serialized_manifest)
        assert manifest["published_city"] == "Atlanta"
        assert "collections" in relations
        assert "languages" in relations
