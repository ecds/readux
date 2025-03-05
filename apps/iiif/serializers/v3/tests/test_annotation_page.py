"""Test Module for IIIF Serializers"""

import json
from apps.readux.models import UserAnnotation
import config.settings.local as settings
from django.test import TestCase
from django.core.serializers import serialize, deserialize
from django.contrib.auth import get_user_model
from apps.iiif.annotations.choices import AnnotationSelector
from apps.iiif.annotations.tests.factories import AnnotationFactory
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.readux.tests.factories import UserAnnotationFactory
from apps.users.tests.factories import UserFactory

User = get_user_model()


class SerializerTests(TestCase):
    def setUp(self):
        self.ocr_user, _ = User.objects.get_or_create(name="OCR", username="ocr")
        self.owner = UserFactory.create()

    def test_annotation_page(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        AnnotationFactory.create(owner=self.ocr_user, canvas=canvas)
        UserAnnotationFactory(canvas=canvas, owner=self.owner)
        UserAnnotationFactory.create(
            canvas=canvas,
            svg="<svg><path></path></svg>",
            primary_selector=AnnotationSelector("SV"),
            owner=self.owner,
        )
        UserAnnotationFactory.create(
            canvas=canvas,
            primary_selector=AnnotationSelector("RG"),
            start_selector=AnnotationFactory.create(canvas=canvas),
            end_selector=AnnotationFactory.create(canvas=canvas),
            start_offset=1,
            end_offset=2,
            content="<p>HTML comment</p>",
            owner=self.owner,
        )

        user_annotations = UserAnnotation.objects.filter(
            owner=self.owner, canvas=canvas
        )

        annotation_count = (
            canvas.annotation_set.count() + canvas.userannotation_set.count()
        )

        serialized_annotation_page = json.loads(
            serialize(
                "annotation_page_v3",
                [canvas],
                annotations=canvas.userannotation_set.all(),
            )
        )

        assert annotation_count == 6
        assert len(serialized_annotation_page["items"]) == 3
        assert (
            f"{canvas.manifest.pid}/annotationpage/{canvas.pid}"
            in serialized_annotation_page["id"]
        )
        assert serialized_annotation_page["id"].startswith("https")


class DeserializerTests(TestCase):
    def test_web_annotation_comment_fragment_deserialization(self):
        user = UserFactory.create()
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        annotation_page = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": "{h}/iiif/{m}/annotationpage/{c}".format(
                h=settings.HOSTNAME, m=canvas.manifest.pid, c=canvas.pid
            ),
            "items": [
                {
                    "type": "Annotation",
                    "body": [
                        {
                            "purpose": "commenting",
                            "type": "TextualBody",
                            "created": "2022-06-06T20:29:08.108Z",
                            "value": "<p>Really smart annotation</p>",
                            "format": "text/html",
                            "creator": {"id": user.username, "name": user.name},
                            "modified": "2022-06-06T20:29:08.108Z",
                        }
                    ],
                    "target": {
                        "source": canvas.resource_id,
                        "selector": {
                            "type": "FragmentSelector",
                            "conformsTo": "http://www.w3.org/TR/media-frags/",
                            "value": "xywh=pixel:575.7898559570312,1263.1917724609375,677.0464477539062,737.7884521484375",
                        },
                    },
                    "@context": "http://www.w3.org/ns/anno.jsonld",
                    "id": "#51602663-36ee-4692-a327-2f438daf48a9",
                }
            ],
        }

        deserialized_annotations = deserialize("annotation_page_v3", annotation_page)

        assert len(deserialized_annotations) == 1

        for item in deserialized_annotations:
            deserialized_annotation, _ = item
            annotation = UserAnnotation(**deserialized_annotation)
            assert annotation.owner == user
            assert annotation.canvas == canvas
            assert annotation.content == annotation_page["items"][0]["body"][0]["value"]
            assert annotation.x == 575.7898559570312
            assert annotation.y == 1263.1917724609375
            assert annotation.w == 677.0464477539062
            assert annotation.h == 737.7884521484375
