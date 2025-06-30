"""Module for serializing IIIF V2 Annotation Lists"""

import json
from re import findall
from bs4 import BeautifulSoup
from django.core.serializers import deserialize
from django.contrib.auth import get_user_model
from apps.iiif.serializers.annotation import Serializer as AnnotationSerializer
from apps.iiif.annotations.models import Annotation
from apps.iiif.annotations.choices import AnnotationPurpose, AnnotationSelector
from apps.iiif.canvases.models import Canvas

USER = get_user_model()


class Serializer(AnnotationSerializer):
    """Convert a queryset to IIIF Annotation"""


def Deserializer(data):  # pylint: disable=invalid-name
    """Deserialize V2 Annotation.

    Args:
        data (dict): V2 IIIF Annotation

    Returns:
        annotation: annotation dict
    """

    if isinstance(data, str):
        data = json.loads(data)

    annotation = {
        "id": data["@id"],
        "owner": USER.objects.get(name=data["annotatedBy"]["name"]),
    }
    tags = []

    if data["motivation"] == "oa:commenting":
        annotation["motivation"] = AnnotationPurpose("CM")

    if data["motivation"] == "oa:painting":
        annotation["motivation"] = AnnotationPurpose("PT")

    source_parts = data["on"]["full"].split("/")
    canvas_pid = source_parts[-1] if source_parts[-1] != "canvas" else source_parts[-2]
    annotation["canvas"] = Canvas.objects.get(pid=canvas_pid)

    resources = (
        data["resource"] if isinstance(data["resource"], list) else [data["resource"]]
    )

    for resource in resources:
        if resource["@type"] == "cnt:ContentAsText":
            annotation["resource_type"] = Annotation.OCR
        if resource["@type"] == "dctypes:Text":
            annotation["resource_type"] = Annotation.TEXT

        if resource["@type"] == "oa:Tag":
            tags.append(resource["chars"])
        else:
            annotation["content"] = resource["chars"]
            soup = BeautifulSoup(resource["chars"], "html.parser")
            annotation["raw_content"] = soup.get_text(separator=" ", strip=True)

    annotation["x"], annotation["y"], annotation["w"], annotation["h"] = [
        float(n) for n in data["on"]["selector"]["value"].split("=")[-1].split(",")
    ]

    if data["on"]["selector"]["item"]["@type"] == "oa:SvgSelector":
        annotation["svg"] = data["on"]["selector"]["item"]["value"]

    if data["on"]["selector"]["item"]["@type"] == "RangeSelector":
        annotation["start_selector"], _ = Annotation.objects.get_or_create(
            id=findall(
                r"([A-Za-z0-9\-]+)",
                data["on"]["selector"]["item"]["startSelector"]["value"],
            )[-1]
        )
        annotation["end_selector"], _ = Annotation.objects.get_or_create(
            id=findall(
                r"([A-Za-z0-9\-]+)",
                data["on"]["selector"]["item"]["endSelector"]["value"],
            )[-1]
        )
        annotation["start_offset"] = data["on"]["selector"]["item"]["startSelector"][
            "refinedBy"
        ]["start"]

        annotation["end_offset"] = data["on"]["selector"]["item"]["endSelector"][
            "refinedBy"
        ]["end"]

    return (
        annotation,
        tags,
    )
