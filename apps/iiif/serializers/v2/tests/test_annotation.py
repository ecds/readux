"""Test Module for IIIF Serializers"""

import os
import json
from django.test import TestCase
from django.core.serializers import serialize, deserialize
from django.contrib.auth import get_user_model
from django.conf import settings
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

        deserialized_annotation, _ = deserialize("annotation_v2", user_annotation)
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

    def test_v2_user_annotation_deserialization(self):
        """It should deserialize v2 user annotations."""
        user = UserFactory.create(name="Dominique Wilkins", username="wilkins")
        CanvasFactory.create(pid="spb1b_000.tif", manifest=ManifestFactory.create())
        with open(
            os.path.join(
                settings.APPS_DIR,
                "iiif",
                "serializers",
                "v2",
                "fixtures",
                "v2_user_annotation_list.json",
            )
        ) as file:
            data = file.read()
            deserialized_annotation, tags = deserialize("annotation_list", data)
            print(deserialized_annotation)
            print(tags)
            assert True

    def test_v2_and_v3_create_identical_user_annotations(self):
        """Both deserializer versions should return identical objects."""
        manifest = ManifestFactory.create()
        canvas = manifest.canvas_set.all()[0]
        annotation = UserAnnotationFactory.create(canvas=canvas)
        v2_serialized_annotation = serialize("annotation_v2", [annotation])
        v3_serialized_annotation = serialize("annotation_v3", [annotation])
        v2_deserialized_annotation, _ = deserialize(
            "annotation", v2_serialized_annotation
        )
        v3_deserialized_annotation, _ = deserialize(
            "annotation", v3_serialized_annotation
        )
        print(v2_deserialized_annotation)
        print(v3_deserialized_annotation)
        for key in v3_deserialized_annotation.keys():
            assert v3_deserialized_annotation[key] == v2_deserialized_annotation[key]
        for key in v2_deserialized_annotation.keys():
            assert v2_deserialized_annotation[key] == v3_deserialized_annotation[key]

    def test_v2_and_v3_create_identical_user_text_annotations(self):
        """Both deserializer versions should return identical objects."""
        UserFactory.create(username="wilkins", name="Dominique Wilkins")
        manifest = ManifestFactory.create()
        canvas = CanvasFactory.create(pid="spb1b_000.tif", manifest=manifest)
        AnnotationFactory.create(
            id="5a1b56bb-b32d-419a-969a-0465982c8a0f", order=1, canvas=canvas
        )
        AnnotationFactory.create(
            id="ece5a9ff-ee53-4106-8177-5b18fe3e1da8", order=4, canvas=canvas
        )
        for n in range(2, 4):
            AnnotationFactory.create(order=n, canvas=canvas)
        v2_anno = None
        v3_anno = None
        with open(
            os.path.join(
                settings.APPS_DIR,
                "iiif",
                "serializers",
                "v2",
                "fixtures",
                "v2_user_annotation_list.json",
            ),
            "r",
            encoding="utf8",
        ) as file:
            v2_anno = json.load(file)["resources"][0]
        with open(
            os.path.join(
                settings.APPS_DIR,
                "iiif",
                "serializers",
                "v3",
                "fixtures",
                "v3_user_annotation_list.json",
            ),
            "r",
            encoding="utf8",
        ) as file:
            v3_anno = json.load(file)["items"][0]

        v2_deserialized_annotation, _ = deserialize("annotation", v2_anno)
        v3_deserialized_annotation, _ = deserialize("annotation", v3_anno)
        print(v2_deserialized_annotation)
        print(v3_deserialized_annotation)
        for key in v3_deserialized_annotation.keys():
            if key == "start_selector" or key == "end_selector":
                assert str(v3_deserialized_annotation[key].id) == str(
                    v2_deserialized_annotation[key].id
                )
            else:
                assert (
                    v3_deserialized_annotation[key] == v2_deserialized_annotation[key]
                )
        for key in v2_deserialized_annotation.keys():
            if key == "start_selector" or key == "end_selector":
                assert str(v2_deserialized_annotation[key].id) == str(
                    v3_deserialized_annotation[key].id
                )
            else:
                assert (
                    v2_deserialized_annotation[key] == v3_deserialized_annotation[key]
                )
