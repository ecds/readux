"""Test Module for IIIF Serializers"""

import json
from django.test import TestCase
from django.core.serializers import serialize, deserialize
from apps.iiif.annotations.models import Annotation
from apps.iiif.annotations.choices import AnnotationPurpose, AnnotationSelector
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
        self.ocr_user, _ = User.objects.get_or_create(name="OCR", username="ocr")

    def test_ocr_annotation(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        ocr_anno = AnnotationFactory.create(owner=self.ocr_user, canvas=canvas)
        serialized_ocr_anno = json.loads(serialize("annotation_v3", [ocr_anno]))

        body = serialized_ocr_anno["body"][0]
        target = serialized_ocr_anno["target"]

        assert body["value"].startswith("<span")
        assert body["value"].endswith("span>")
        assert body["format"] == "text/html"
        assert "data-letter-spacing" in body["value"]
        assert body["creator"] == {"id": "ocr", "name": "OCR"}
        assert target["source"] == canvas.resource_id
        assert (
            target["selector"]["value"]
            == f"xywh=pixel:{ocr_anno.x},{ocr_anno.y},{ocr_anno.w},{ocr_anno.h}"
        )
        assert target["selector"]["type"] == AnnotationSelector("FR").name
        assert len(serialized_ocr_anno["body"]) == 1

    def test_fragment_annotation(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        frag_anno = UserAnnotationFactory(canvas=canvas)
        serialized_frag_anno = json.loads(serialize("annotation_v3", [frag_anno]))
        body = serialized_frag_anno["body"][0]
        target = serialized_frag_anno["target"]

        assert body["value"] == frag_anno.content
        assert body["format"] == "text/plain"
        assert body["creator"] == {
            "id": frag_anno.owner.username,
            "name": frag_anno.owner.name,
        }
        assert target["source"] == canvas.resource_id
        assert (
            target["selector"]["value"]
            == f"xywh=pixel:{frag_anno.x},{frag_anno.y},{frag_anno.w},{frag_anno.h}"
        )
        assert target["selector"]["type"] == AnnotationSelector("FR").name
        assert len(serialized_frag_anno["body"]) == 1

    def test_svg_annotation(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        svg_anno = UserAnnotationFactory.create(
            canvas=canvas,
            svg="<svg><path></path></svg>",
            primary_selector=AnnotationSelector("SV"),
        )
        serialized_svg_anno = json.loads(serialize("annotation_v3", [svg_anno]))
        body = serialized_svg_anno["body"][0]
        svg_target = serialized_svg_anno["target"]

        assert body["value"] == svg_anno.content
        assert body["format"] == "text/plain"
        assert body["creator"] == {
            "id": svg_anno.owner.username,
            "name": svg_anno.owner.name,
        }
        assert svg_target["source"] == canvas.resource_id
        assert svg_target["selector"]["value"] == svg_anno.svg
        assert svg_target["selector"]["type"] == AnnotationSelector("SV").name
        assert len(serialized_svg_anno["body"]) == 1

    def test_text_annotation(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        text_anno = UserAnnotationFactory.create(
            canvas=canvas,
            primary_selector=AnnotationSelector("RG"),
            start_selector=AnnotationFactory.create(canvas=canvas),
            end_selector=AnnotationFactory.create(canvas=canvas),
            start_offset=1,
            end_offset=2,
            content="<p>HTML comment</p>",
        )

        serialized_text_anno = json.loads(serialize("annotation_v3", [text_anno]))
        body = serialized_text_anno["body"][0]
        text_target = serialized_text_anno["target"]

        assert len(serialized_text_anno["body"]) == 1
        assert body["value"] == text_anno.content
        assert body["format"] == "text/html"
        assert body["creator"] == {
            "id": text_anno.owner.username,
            "name": text_anno.owner.name,
        }
        assert text_target["source"] == canvas.resource_id
        assert (
            text_target["selector"]["startSelector"]["value"]
            == f"//*[@id='{text_anno.start_selector.pk}']"
        )
        assert (
            text_target["selector"]["endSelector"]["value"]
            == f"//*[@id='{text_anno.end_selector.pk}']"
        )
        assert (
            text_target["selector"]["startSelector"]["refinedBy"]["start"]
            == text_anno.start_offset
        )
        assert (
            text_target["selector"]["endSelector"]["refinedBy"]["end"]
            == text_anno.end_offset
        )
        assert text_target["selector"]["type"] == AnnotationSelector("RG").name


class DeserializerTests(TestCase):

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

        deserialized_annotation, _ = deserialize("annotation_v3", web_annotation)
        annotation = UserAnnotation(**deserialized_annotation)
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
                    "format": "text/html",
                    "creator": {"id": user.username, "name": user.name},
                    "modified": "2022-06-06T20:38:37.123Z",
                },
                {
                    "type": "TextualBody",
                    "value": "Tag One",
                    "purpose": "tagging",
                    "format": "text/plain",
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

        deserialized_annotation, tags = deserialize("annotation_v3", web_annotation)
        annotation = UserAnnotation(**deserialized_annotation)
        annotation.save()
        for tag in tags:
            annotation.tags.add(tag)
        assert annotation.owner == user
        assert annotation.canvas == canvas
        assert annotation.content == web_annotation["body"][0]["value"]
        assert annotation.raw_content == "Even smarter annotation"
        assert "Tag One" in annotation.tag_list
        assert annotation.svg
        assert annotation.x == 448.96453857421875
        assert annotation.y == 1384.190185546875
        assert annotation.w == 1224.1728515625
        assert annotation.h == 1224.173095703125

    def test_web_annotation_comment_range_deserialization(self):
        user = UserFactory.create()
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        start = AnnotationFactory.create(canvas=canvas, order=3)
        end = AnnotationFactory.create(canvas=canvas, order=15)
        web_annotation = {
            "type": "Annotation",
            "body": [
                {
                    "type": "TextualBody",
                    "value": "<p>Yet another annotation</p>",
                    "purpose": "commenting",
                    "format": "text/html",
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

        annotation_attrs, _ = deserialize("annotation_v3", web_annotation)
        annotation = UserAnnotation.objects.create(**annotation_attrs)
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

    def test_deserialization_update(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        svg_anno = UserAnnotationFactory.create(
            canvas=canvas,
            svg="<svg><path></path></svg>",
            primary_selector=AnnotationSelector("SV"),
            purpose=AnnotationPurpose("CM"),
        )
        serialized_svg_anno = json.loads(serialize("annotation_v3", [svg_anno]))
        body = serialized_svg_anno["body"][0]
        new_content = "some updated content"

        assert serialized_svg_anno["body"][0]["value"] == svg_anno.content
        assert serialized_svg_anno["id"].replace("#", "") == str(svg_anno.id)
        assert svg_anno.content != new_content
        serialized_svg_anno["body"][0]["value"] = new_content

        serialized_svg_anno["body"].append(
            {
                "type": "TextualBody",
                "purpose": "tagging",
                "format": "text/plain",
                "value": "awesome",
            }
        )

        updated_anno_attrs, tags = deserialize("annotation_v3", serialized_svg_anno)

        svg_anno.update(updated_anno_attrs, tags)
        svg_anno.refresh_from_db()

        assert svg_anno.content == new_content
        assert tags == ["awesome"]
