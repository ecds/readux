# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF User Annotation Lists"""
import json
from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers import serialize
from apps.iiif.serializers.annotation_list import (
    Serializer as IIIFAnnotationListSerializer,
)
import config.settings.local as settings


class Serializer(IIIFAnnotationListSerializer):
    """
    IIIF V2 Annotation List https://iiif.io/api/presentation/2.1/#annotation-list
    """

    def get_dump_object(self, obj):
        if (self.version == "v2") or (self.version is None):
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": "{h}/annotations/{u}/{m}/list/{c}".format(
                    h=settings.HOSTNAME,
                    u=self.owners[0].username,
                    m=obj.manifest.pid,
                    c=obj.pid,
                ),
                "@type": "sc:AnnotationList",
                "resources": json.loads(
                    serialize(
                        "annotation",
                        obj.userannotation_set.filter(owner__in=[self.owners[0].id]),
                        is_list=True,
                    )
                ),
            }
            return data
        return None


class Deserializer:
    """Deserialize IIIF Annotation List

    :raises SerializerDoesNotExist: Not yet implemented.
    """

    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist(
            "user_annotation_list is a serialization-only serializer"
        )
