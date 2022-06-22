"""Test Module for IIIF Serializers"""
import json
from random import randint
from django.test import TestCase
from django.core.serializers import serialize, deserialize
from apps.iiif.annotations.models import Annotation
from apps.iiif.annotations.choices import AnnotationSelector
from apps.iiif.annotations.tests.factories import AnnotationFactory
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.readux.models import UserAnnotation
from apps.readux.tests.factories import UserAnnotationFactory
from apps.users.tests.factories import UserFactory
from django.contrib.auth import get_user_model

User = get_user_model()

class SerializerTests(TestCase):
    def setUp(self):
        """_summary_
        """
        pass

    def test_manifest(self):
        manifest = ManifestFactory.create()
        user = UserFactory.create()
        for _ in range(0,10):
            canvas = CanvasFactory.create(manifest=manifest)
            for _ in range(0, randint(3,5)):
                AnnotationFactory.create(canvas=canvas)
            for _ in range(0, randint(3,5)):
                UserAnnotationFactory.create(canvas=canvas, owner=user)

        serialized_manifest = json.loads(
            serialize(
                'manifest_v3',
                [manifest],
                current_user=user
            )
        )

        assert 1 == 1
