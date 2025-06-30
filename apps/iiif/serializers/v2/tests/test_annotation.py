"""Test Module for IIIF Serializers"""

import json
from random import randint
from django.test import TestCase
from django.core.serializers import serialize, deserialize
from django.contrib.auth import get_user_model
from apps.iiif.annotations.tests.factories import AnnotationFactory
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.iiif.annotations.models import Annotation
from apps.readux.tests.factories import UserAnnotationFactory
from apps.users.tests.factories import UserFactory

User = get_user_model()


class AnnotationSerializerTests(TestCase):
    def setUp(self):
        """_summary_"""
        self.annotation = Annotation()

    def test_user_annotation_svg_comment_fragment_deserialization(self):
        user = UserFactory.create()
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        user_annotation = UserAnnotationFactory.create(
            owner=user,
            canvas=canvas,
            svg='<svg xmlns=\'http://www.w3.org/2000/svg\'><path xmlns="http://www.w3.org/2000/svg" d="M776.61589,691.19186c79.13019" />',
            x=1.8,
            y=2.7,
            w=3.6,
            h=4.5,
            content="my smart annotation",
        )
        web_annotation = serialize("annotation_v2", [user_annotation])
        print(web_annotation)

        deserialized_annotation, _ = deserialize("annotation_v2", web_annotation)
        assert deserialized_annotation["owner"] == user
        assert deserialized_annotation["canvas"] == canvas
        assert deserialized_annotation["svg"] == user_annotation.svg
        assert deserialized_annotation["content"] == "my smart annotation"
        assert deserialized_annotation["x"] == 1.8
        assert deserialized_annotation["y"] == 2.7
        assert deserialized_annotation["w"] == 3.6
        assert deserialized_annotation["h"] == 4.5

    def test_user_annotation_text_highlight_deserialization(self):
        user = UserFactory.create()
        manifest = ManifestFactory.create()
        user_annotation = {
            "@context": "http://iiif.io/api/presentation/2/context.json",
            "@id": "4e268523-7898-4344-a2c9-4036ea3bf965",
            "@type": "oa:Annotation",
            "motivation": ["oa:commenting", "oa:tagging"],
            "annotatedBy": {"name": user.name},
            "resource": [
                {
                    "@type": "dctypes:Text",
                    "format": "text/html",
                    "chars": "<p>text anno</p>",
                    "language": "en",
                },
                {"@type": "oa:Tag", "chars": "Amazing"},
            ],
            "on": {
                "full": f"https://readux.io/iiif/v2/{manifest.pid}/canvas/{manifest.canvas_set.all()[0].pid}",
                "@type": "oa:SpecificResource",
                "within": {
                    "@id": f"https://readux.io/iiif/v2/{manifest.pid}/manifest",
                    "@type": "sc:Manifest",
                },
                "selector": {
                    "@type": "oa:FragmentSelector",
                    "value": "xywh=1378,4130,602,94",
                    "item": {
                        "@type": "RangeSelector",
                        "startSelector": {
                            "@type": "XPathSelector",
                            "value": "//*[@id='a7293772-7218-4a68-a011-86551ac84ed2']",
                            "refinedBy": {"@type": "TextPositionSelector", "start": 3},
                        },
                        "endSelector": {
                            "@type": "XPathSelector",
                            "value": "//*[@id='a0a585e2-c30f-437f-b18c-36986cfa6e9f']",
                            "refinedBy": {"@type": "TextPositionSelector", "end": 9},
                        },
                    },
                },
            },
            "stylesheet": {
                "type": "CssStylesheet",
                "value": ".anno-4e268523-7898-4344-a2c9-4036ea3bf965 { background: rgba(0, 191, 255, 0.5); }",
            },
        }

        deserialized_annotation, tags = deserialize("annotation_v2", user_annotation)
        assert deserialized_annotation["id"] == user_annotation["@id"]
        assert deserialized_annotation["owner"] == user
        assert deserialized_annotation["canvas"] == manifest.canvas_set.all()[0]
        assert deserialized_annotation["resource_type"] == self.annotation.TEXT
        assert deserialized_annotation["content"] == "<p>text anno</p>"
        assert deserialized_annotation["raw_content"] == "text anno"
        assert deserialized_annotation["x"] == 1378.0
        assert deserialized_annotation["y"] == 4130.0
        assert deserialized_annotation["w"] == 602.0
        assert deserialized_annotation["h"] == 94.0
        assert str(deserialized_annotation["start_selector"].id) == str(
            Annotation.objects.get(id="a7293772-7218-4a68-a011-86551ac84ed2").id
        )
        assert str(deserialized_annotation["end_selector"].id) == str(
            Annotation.objects.get(id="a0a585e2-c30f-437f-b18c-36986cfa6e9f").id
        )
        assert deserialized_annotation["start_offset"] == 3
        assert deserialized_annotation["end_offset"] == 9
        # assert False
