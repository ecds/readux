# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Canvas"""
from django.urls import reverse
import config.settings.local as settings
from apps.iiif.serializers.base import Serializer as JSONSerializer


class Serializer(JSONSerializer):
    """
    Convert a queryset to IIIF Canvas
    """

    def _init_options(self):
        super()._init_options()
        self.current_user = self.json_kwargs.pop("current_user", None)

    def get_dump_object(self, obj):
        kwargs = {
            "username": "ocr",
            "vol": obj.manifest.pid,
            "canvas": obj.pid,
            "version": "v3",
        }

        ocr_uri = "{h}{k}".format(
            h=settings.HOSTNAME, k=reverse("user_comments", kwargs=kwargs)
        )

        data = {
            "id": f"{obj.v3_baseurl}/canvas",
            "type": "Canvas",
            "label": obj.label,
            "height": obj.height,
            "width": obj.width,
            "items": [
                {
                    "id": f"{obj.v3_baseurl}/page/{obj.position}",
                    "type": "Annotation",
                    "motivation": "painting",
                    "body": {
                        "id": obj.resource_id,
                        "type": "Image",
                        "format": "image/jpeg",
                        "height": obj.height,
                        "width": obj.width,
                    },
                }
            ],
            "annotations": [{"type": "AnnotationPage", "id": ocr_uri}],
        }

        if self.current_user and self.current_user.username != "":
            kwargs["username"] = self.current_user.username
            user_annotations_uri = "{h}{k}".format(
                h=settings.HOSTNAME, k=reverse("user_comments", kwargs=kwargs)
            )

            data["annotations"].append(
                {"type": "AnnotationPage", "id": user_annotations_uri}
            )

        return data


def Deserializer(data):
    """
    Deserialize IIIF v3 Manifest
    """
    return {
        "pid": data["id"].split("/")[-2],
        "resource": data["id"].split("/")[-2],
        "width": data["width"],
        "height": data["height"],
    }
