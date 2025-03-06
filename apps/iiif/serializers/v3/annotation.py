# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation"""
from bs4 import BeautifulSoup
from re import findall
from django.contrib.auth import get_user_model
from apps.iiif.serializers.base import Serializer as JSONSerializer
from apps.iiif.annotations.models import Annotation
from apps.iiif.annotations.choices import AnnotationPurpose, AnnotationSelector
from apps.iiif.canvases.models import Canvas
from apps.readux.models import UserAnnotation

USER = get_user_model()


class Serializer(JSONSerializer):
    """
    Serialize objects based on :class:`apps.iiif.annotation.models.AnnotationAbstract`
    Serialization conforms to the Web Annotation Data Model
    https://www.w3.org/TR/annotation-model/#annotations
    """

    # def _init_options(self):
    #     super()._init_options()

    def get_dump_object(self, obj):
        """
        Serialize an :class:`apps.iiif.annotation.models.Annotation`
        Serialization conforms to the Web Annotation Data Model
        https://www.w3.org/TR/annotation-model/#annotations

        {
            "type": "Annotation",
            "body": [
                {
                    "purpose": "commenting",
                    "type": "TextualBody",
                    "created": "2022-06-06T20:38:37.123Z",
                    "value": "<p>Super smart annotation</p>",
                    "format": "text/html",
                    "creator": {
                        "id": "jay",
                        "name": "Jay S. Varner"
                    },
                    "modified": "2022-06-06T20:38:37.123Z"
                },
                {
                    "type": "TextualBody",
                    "value": "aaaaa",
                    "purpose": "tagging",
                    "formate": "text/plain",
                    "creator": {
                        "id": "jay",
                        "name": "Jay S. Varner"
                    },
                    "created": "2022-06-06T20:38:43.052Z",
                    "modified": "2022-06-06T20:38:43.720Z"
                }
            ],
            "target": {
                "source": "https://iip.readux.io/iiif/2/t4vc6_00000009.tif",
                "selector": {
                    "type": "SvgSelector",
                    "value": "<svg><circle cx=\"837.1289215087891\" cy=\"2624.0111083984375\" r=\"558.2640706617552\"></circle></svg>"
                }
            },
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": "#db7cd136-cdb7-4b1e-b33c-f0afd66c1aee"
        }

        :param obj: Annotation to be serialized.
        :type obj: :class:`apps.iiif.annotation.models.Annotation`
        :return: Serialized annotation.
        :rtype: dict
        """

        creator = {"id": obj.owner.username, "name": obj.owner.name}

        base_body = {
            "creator": creator,
            "created": obj.created_at_iso,
            "modified": obj.modified_at_iso,
        }

        data = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"#{obj.pk}",
            "type": "Annotation",
            "body": [],
            "target": {
                "source": obj.canvas.resource_id,
                "selector": {"type": AnnotationSelector(obj.primary_selector).name},
            },
        }

        if obj.content:
            content_body = {
                "type": "TextualBody",
                "value": obj.content,
                "purpose": AnnotationPurpose(obj.purpose).name,
                "format": "text/html" if obj.content_is_html else "text/plain",
                **base_body,
            }

            data["body"].append(content_body)

        if obj.primary_selector == "SV":
            data["target"]["selector"]["value"] = obj.svg

        if obj.primary_selector == "RG" and isinstance(obj, UserAnnotation):
            range_selector = {
                "startSelector": {
                    "type": AnnotationSelector("XP").name,
                    "value": f"//*[@id='{obj.start_selector.pk}']",
                    "refinedBy": {
                        "type": AnnotationSelector("TP").name,
                        "start": obj.start_offset,
                    },
                },
                "endSelector": {
                    "type": AnnotationSelector("XP").name,
                    "value": f"//*[@id='{obj.end_selector.pk}']",
                    "refinedBy": {
                        "type": AnnotationSelector("TP").name,
                        "end": obj.end_offset,
                    },
                },
            }

            data["target"]["selector"] = {
                **data["target"]["selector"],
                **range_selector,
            }

        if hasattr(obj, "tag_list"):
            for anno_tag in obj.tag_list:
                data["body"].append(
                    {
                        "type": "TextualBody",
                        "value": anno_tag,
                        "purpose": AnnotationPurpose("TG").name,
                        **base_body,
                    }
                )

        if obj.primary_selector == "FR":
            data["target"]["selector"]["value"] = obj.fragment
            data["target"]["selector"][
                "conformsTo"
            ] = "http://www.w3.org/TR/media-frags/"
        else:
            fragment_selector = {
                "source": obj.canvas.resource_id,
                "selector": {
                    "type": AnnotationSelector("FR").name,
                    "value": obj.fragment,
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                },
            }

            # data['targets'].append(fragment_selector)

        return data
        # return None

    # TODO: is this needed?
    @classmethod
    def __serialize_item(cls, obj):
        return obj.item


def Deserializer(data):
    annotation = {}
    annotation["owner"] = USER.objects.get(username=data["body"][0]["creator"]["id"])
    source_parts = data["target"]["source"].split("/")
    canvas_pid = source_parts[-1] if source_parts[-1] != "canvas" else source_parts[-2]
    annotation["canvas"] = Canvas.objects.get(pid=canvas_pid)
    tags = []

    for body in data["body"]:
        if body["purpose"] == "commenting":
            annotation["content"] = body["value"]
            annotation["purpose"] = AnnotationPurpose("CM")
        if body["purpose"] == "tagging":
            tags.append(body["value"])
        if body["type"] == "TextualBody" and body["format"] == "text/html":
            annotation["content"] = body["value"]
            soup = BeautifulSoup(body["value"], "html.parser")
            annotation["raw_content"] = soup.get_text(separator=" ", strip=True)
        if data["body"][0]["creator"]["id"] == "OCR":
            annotation["resource_type"] = Annotation.OCR

    annotation["primary_selector"] = AnnotationSelector[
        data["target"]["selector"]["type"]
    ]

    if data["target"]["selector"]["type"] == "SvgSelector":
        annotation["svg"] = data["target"]["selector"]["value"]

        if (
            "refinedBy" in data["target"]["selector"]
            and data["target"]["selector"]["refinedBy"]["type"] == "FragmentSelector"
        ):
            annotation["x"], annotation["y"], annotation["w"], annotation["h"] = [
                float(n)
                for n in data["target"]["selector"]["refinedBy"]["value"]
                .split("=")[-1]
                .split(",")
            ]

    if data["target"]["selector"]["type"] == "FragmentSelector":
        annotation["x"], annotation["y"], annotation["w"], annotation["h"] = [
            float(n)
            for n in data["target"]["selector"]["value"].split(":")[-1].split(",")
        ]

    if data["target"]["selector"]["type"] == "RangeSelector":
        annotation["start_selector"] = Annotation.objects.get(
            id=findall(
                r"([A-Za-z0-9\-]+)",
                data["target"]["selector"]["startSelector"]["value"],
            )[-1]
        )
        annotation["end_selector"] = Annotation.objects.get(
            id=findall(
                r"([A-Za-z0-9\-]+)", data["target"]["selector"]["endSelector"]["value"]
            )[-1]
        )
        annotation["start_offset"] = data["target"]["selector"]["startSelector"][
            "refinedBy"
        ]["start"]
        annotation["end_offset"] = data["target"]["selector"]["endSelector"][
            "refinedBy"
        ]["end"]

        start_position = annotation["start_selector"].order
        end_position = annotation["end_selector"].order
        text = Annotation.objects.filter(
            canvas=annotation["canvas"],
            order__lt=end_position,
            order__gte=start_position,
        ).order_by("order")

        try:
            annotation["x"] = min(text.values_list("x", flat=True))
            annotation["y"] = max(text.values_list("y", flat=True))
            annotation["h"] = max(text.values_list("h", flat=True))
            annotation["w"] = text.last().x + text.last().w - annotation["x"]
        except ValueError:
            pass

    return (
        annotation,
        tags,
    )
