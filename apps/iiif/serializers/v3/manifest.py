"""Module for serializing IIIF Annotation Lists"""

import re
import json
from datetime import datetime
from django.core.serializers import serialize
from apps.iiif.manifests.models import Manifest
from apps.iiif.canvases.models import Canvas
from apps.iiif.serializers.base import Serializer as JSONSerializer


class Serializer(JSONSerializer):
    """
    Convert a queryset to IIIF Manifest
    """

    def _init_options(self):
        super()._init_options()
        self.current_user = self.json_kwargs.pop("current_user", None)

    def get_dump_object(self, obj):
        try:
            thumbnail = f"{obj.image_server.server_base}/{obj.start_canvas.resource}"
        except (Canvas.MultipleObjectsReturned, Canvas.DoesNotExist):
            thumbnail = f"{obj.image_server.server_base}/{obj.canvas_set.all().first().resource}"

        metadata = []
        if len(obj.metadata) > 0:
            if isinstance(obj.metadata, dict):
                metadata.append(obj.metadata)
            if isinstance(obj.metadata, list):
                metadata += obj.metadata

        if obj.author is not None:
            metadata.append({"label": "Author", "value": obj.author})

        if obj.published_city is not None:
            metadata.append({"label": "Published City", "value": obj.published_city})

        if obj.published_date is not None:
            metadata.append({"label": "Published Date", "value": obj.published_date})

        if obj.published_date_edtf is not None:
            metadata.append(
                {"label": "Published Date EDTF", "value": str(obj.published_date_edtf)}
            )

        if obj.languages.count() > 0 is not None:
            metadata.append(
                {
                    "label": "Languages",
                    "value": [lng.code for lng in obj.languages.all()],
                }
            )

        if obj.collections.count() > 0 is not None:
            metadata.append(
                {
                    "label": "Collections",
                    "value": [col.label for col in obj.collections.all()],
                }
            )

        data = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": f"{obj.v3_baseurl}/manifest",
            "type": "Manifest",
            "label": obj.label,
            "metadata": metadata,
            "summary": {"none": [obj.summary]},
            "viewingDirection": obj.viewingdirection,
            "rights": obj.license,
            "thumbnail": [
                {
                    "id": f"{thumbnail}/full/600,/0/default.jpg",
                    "type": "Image",
                    "format": "image/jpeg",
                    "service": [
                        {"id": thumbnail, "type": "ImageService3", "profile": "level1"}
                    ],
                }
            ],
            "items": [],
        }

        if obj.pdf:
            data["rendering"] = [
                {
                    "id": obj.pdf,
                    "type": "Text",
                    "label": {"en": ["Download as PDF"]},
                    "format": "application/pdf",
                }
            ]

        for canvas in obj.canvas_set.all():
            data["items"].append(
                json.loads(
                    serialize("canvas_v3", [canvas], current_user=self.current_user)
                )
            )

        return data


def Deserializer(data):
    """
    Deserialize IIIF v3 Manifest
    """
    manifest = {
        "pid": data["id"].split("/")[-2],
        "viewingdirection": data["viewingDirection"],
        "license": data["rights"],
    }

    if "rendering" in data:
        for renderer in data["rendering"]:
            if "pdf" in renderer["format"]:
                manifest["pdf"] = renderer["id"]

    relations = {}

    fields = [f.name for f in Manifest._meta.get_fields()]

    for key, value in data.items():
        if key in fields and key != "id":
            if key == "metadata":
                manifest["metadata"] = []
                if isinstance(data["metadata"], list):
                    for attr in data["metadata"]:
                        if isinstance(attr, dict):
                            key = attr["label"]
                            field = re.sub(r"\([^)]*\)", "", key).strip()
                            field = field.replace(" ", "_")
                            field = field.lower()
                            if field in fields:
                                if field == "published_date":
                                    date = __parse_date(attr["value"])
                                    if date is not None:
                                        manifest[field] = date
                                    else:
                                        manifest["published_date_edtf"] = attr["value"]
                                elif field == "collections" or field == "languages":
                                    relations[field] = attr["value"]
                                else:
                                    manifest[field] = attr["value"]
                            else:
                                manifest["metadata"].append(attr)
            elif isinstance(value, str):
                manifest[key] = value
            elif isinstance(value, dict) and len(value.keys()) > 0:
                if "en" in value.keys():
                    manifest[key] = value["en"][0]
                elif "none" in value.keys():
                    manifest[key] = value["none"][0]
                else:
                    manifest[key] = value[value.keys()[0]]

    return (manifest, relations)


def __parse_date(date):
    parts = [date, 1, 1]
    if "/" in date:
        parts = parts[0].split("/")
    elif "-" in date:
        parts = parts[0].split("-")

    try:
        return datetime(*[int(part) for part in parts])
    except ValueError:
        return None
