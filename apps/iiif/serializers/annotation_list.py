# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation Lists"""
import json
from django.core.serializers import serialize, deserialize
from .base import Serializer as JSONSerializer
from django.contrib.auth import get_user_model
from django.db.models import Q
import config.settings.local as settings

USER = get_user_model()


class Serializer(JSONSerializer):
    """
    IIIF V2 Annotation List https://iiif.io/api/presentation/2.1/#annotation-list
    """

    def _init_options(self):
        super()._init_options()
        self.owners = self.json_kwargs.pop("owners", 0)

    def get_dump_object(self, obj):
        # TODO: Add more validation checks before trying to serialize.
        if self.version == "v2" or self.version is None:
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": "{h}/iiif/v2/{m}/list/{c}".format(
                    h=settings.HOSTNAME, m=obj.manifest.pid, c=obj.pid
                ),
                "@type": "sc:AnnotationList",
                "resources": json.loads(
                    serialize(
                        "annotation",
                        obj.annotation_set.filter(
                            Q(owner=USER.objects.get(username="ocr"))
                            | Q(owner__in=self.owners)
                        ),
                        is_list=True,
                    )
                ),
            }
            return data
        return None


def Deserializer(data):
    """Deserialize IIIF V2 Annotation List"""
    if isinstance(data, str):
        data = json.loads(data)

    if "@context" in data.keys() and "2/context.json" in data["@context"]:
        return [
            deserialize("annotation", annotation) for annotation in data["resources"]
        ]

    return [deserialize("annotation", annotation) for annotation in data["items"]]
