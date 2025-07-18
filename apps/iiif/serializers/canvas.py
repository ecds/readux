# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Canvas"""
import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.serializers import deserialize
import config.settings.local as settings
from apps.iiif.serializers.base import Serializer as JSONSerializer

USER = get_user_model()


class Serializer(JSONSerializer):
    """
    Convert a queryset to IIIF Canvas
    """

    def _init_options(self):
        super()._init_options()
        self.current_user = self.json_kwargs.pop("current_user", None)

    def get_dump_object(self, obj):
        obj.label = str(obj.position)
        if (self.version == "v2") or (self.version is None):

            ocr_web_annotation_path = reverse(
                "web_annotation_ocr",
                kwargs={"volume": obj.manifest.pid, "canvas": obj.pid},
            )

            otherContent = [  # pylint: disable=invalid-name
                {
                    "@id": "{m}/list/{c}".format(m=obj.manifest.baseurl, c=obj.pid),
                    "@type": "sc:AnnotationList",
                    "label": "OCR Text",
                }
            ]

            current_user_has_annotations = (
                self.current_user
                and self.current_user.is_authenticated
                and self.current_user.userannotation_set.filter(canvas=obj).exists()
            )
            if current_user_has_annotations:
                kwargs = {
                    "username": self.current_user.username,
                    "volume": obj.manifest.pid,
                    "canvas": obj.pid,
                }
                annotation_list_url = "{h}{k}".format(
                    h=settings.HOSTNAME, k=reverse("user_annotations", kwargs=kwargs)
                )

                otherContent.append(
                    {
                        "label": f"Annotations by {self.current_user.username}",
                        "@type": "sc:AnnotationList",
                        "@id": annotation_list_url,
                    }
                )

            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": obj.identifier,
                "@type": "sc:Canvas",
                "label": obj.label,
                "height": obj.height,
                "width": obj.width,
                "images": [
                    {
                        "@context": "http://iiif.io/api/presentation/2/context.json",
                        "@id": str(obj.anno_id),
                        "@type": "oa:Annotation",
                        "motivation": "sc:painting",
                        "resource": {
                            "@id": "{id}/full/full/0/default.jpg".format(
                                id=obj.resource_id
                            ),
                            "@type": "dctypes:Image",
                            "format": "image/jpeg",
                            "height": obj.height,
                            "width": obj.width,
                            "service": {
                                "@context": "https://iiif.io/api/image/2/context.json",
                                "@id": obj.resource_id,
                                "profile": "https://iiif.io/api/image/2/level2.json",
                            },
                        },
                        "on": obj.identifier,
                    }
                ],
                "thumbnail": {"@id": obj.thumbnail, "height": 250, "width": 200},
                "otherContent": otherContent,
            }
            return data
        # TODO: Should probably return a helpful error.
        return None


def Deserializer(data):
    """Deserialize IIIF Canvas"""

    if isinstance(data, str):
        data = json.loads(data)

    if "@context" in data and "2/context.json" in data["@context"]:
        return deserialize("canvas_v2", data)

    return deserialize("canvas_v3", data)
