"""Test Module for IIIF Serializers"""

from django.test import TestCase
from django.core.serializers import serialize, deserialize, SerializerDoesNotExist
from apps.iiif.annotations.models import Annotation
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.users.tests.factories import UserFactory


class SerializerTests(TestCase):
    serializers = [
        "annotation_list",
        "annotation",
        "canvas",
        "collection_manifest",
        "kollection",
        "manifest",
        "user_annotation_list",
    ]

    fixtures = [
        "users.json",
        "kollections.json",
        "manifests.json",
        "canvases.json",
        "annotations.json",
    ]

    def test_no_deserialization(self):
        """Deserialization should raise for serialization only error."""
        for serializer in self.serializers:
            if serializer != "annotation":
                try:
                    deserialize(serializer, {})
                except SerializerDoesNotExist as error:
                    assert str(
                        error
                    ) == "'{s} is a serialization-only serializer'".format(s=serializer)

    def test_empty_object(self):
        """If specified version is not implemented, serializer returns an empty dict."""
        for serializer in self.serializers:
            obj = serialize(
                serializer, Canvas.objects.all(), version="Some Random Version"
            )
            assert "null" in obj

    def test_web_annotation_comment_fragment_deserialization(self):
        user = UserFactory.create()
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        web_annotation = {
            "type": "Annotation",
            "body": [
                {
                    "purpose": "commenting",
                    "type": "TextualBody",
                    "created": "2022-06-06T20:29:08.108Z",
                    "format": "text/html",
                    "value": "<p>Really smart annotation</p>",
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

        annotation = deserialize("annotation", web_annotation)
        assert annotation.owner == user
        assert annotation.canvas == canvas
        assert annotation.content == web_annotation["body"][0]["value"]
        assert annotation.x == 575.7898559570312
        assert annotation.y == 1263.1917724609375
        assert annotation.w == 677.0464477539062
        assert annotation.h == 737.7884521484375

    def test_web_annotation_comment_svg_deserialization(self):
        user = UserFactory.create()
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        web_annotation = {
            "type": "Annotation",
            "body": [
                {
                    "purpose": "commenting",
                    "type": "TextualBody",
                    "created": "2022-06-06T20:38:37.123Z",
                    "value": "<p>Even smarter annotation</p>",
                    "creator": {"id": user.username, "name": user.name},
                    "modified": "2022-06-06T20:38:37.123Z",
                },
                {
                    "type": "TextualBody",
                    "value": "Tag One",
                    "purpose": "tagging",
                    "creator": {"id": user.username, "name": user.name},
                    "created": "2022-06-06T20:38:43.052Z",
                    "modified": "2022-06-06T20:38:43.720Z",
                },
            ],
            "target": {
                "source": canvas.resource_id,
                "selector": {
                    "type": "SvgSelector",
                    "value": '<svg><circle cx="837.1289215087891" cy="2624.0111083984375" r="558.2640706617552"></circle></svg>',
                    "refinedBy": {
                        "type": "FragmentSelector",
                        "value": "xywh=448.96453857421875,1384.190185546875,1224.1728515625,1224.173095703125",
                    },
                },
            },
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": "#db7cd136-cdb7-4b1e-b33c-f0afd66c1aee",
        }

        annotation = deserialize("annotation", web_annotation)
        assert annotation.owner == user
        assert annotation.canvas == canvas
        assert annotation.content == web_annotation["body"][0]["value"]
        assert "Tag One" in annotation.tag_list
        assert annotation.svg
        assert annotation.x == 448.96453857421875
        assert annotation.y == 1384.190185546875
        assert annotation.w == 1224.1728515625
        assert annotation.h == 1224.173095703125

    def test_web_annotation_comment_range_deserialization(self):
        user = UserFactory.create()
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        start = Annotation.objects.all().first()
        end = Annotation.objects.all().last()
        web_annotation = {
            "type": "Annotation",
            "body": [
                {
                    "type": "TextualBody",
                    "value": "<p>Yet another annotation</p>",
                    "purpose": "commenting",
                    "creator": {"id": user.username, "name": user.name},
                }
            ],
            "target": {
                "source": canvas.resource_id,
                "selector": {
                    "type": "RangeSelector",
                    "startSelector": {
                        "@type": "XPathSelector",
                        "value": f"//*[@id='{start.pk}']",
                        "refinedBy": {"@type": "TextPositionSelector", "start": 1},
                    },
                    "endSelector": {
                        "type": "XPathSelector",
                        "value": f"//*[@id='{end.pk}']",
                        "refinedBy": {"@type": "TextPositionSelector", "end": 5},
                    },
                },
            },
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": "#da324841-beaa-4710-858e-f128580c6f2d",
        }
        annotation = deserialize("annotation", web_annotation)
        assert annotation.owner == user
        assert annotation.canvas == canvas
        assert annotation.content == web_annotation["body"][0]["value"]
        assert annotation.start_selector == start
        assert (
            annotation.start_offset
            == web_annotation["target"]["selector"]["startSelector"]["refinedBy"][
                "start"
            ]
        )
        assert annotation.end_selector == end
        assert (
            annotation.end_offset
            == web_annotation["target"]["selector"]["endSelector"]["refinedBy"]["end"]
        )
