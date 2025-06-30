# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Collection Lists"""
from django.core.serializers.base import SerializerDoesNotExist
import config.settings.local as settings
from apps.iiif.serializers.base import Serializer as JSONSerializer


class Serializer(JSONSerializer):
    """IIIF Collection"""

    def get_dump_object(self, obj):
        if (self.version == "v2") or (self.version is None):
            data = {
                "@id": "{h}/iiif/{p}/manifest".format(h=settings.HOSTNAME, p=obj.pid),
                "@type": "sc:Manifest",
                "label": obj.label,
            }
            return data
        return None


class Deserializer:
    """Deserialize IIIF Annotation List

    :raises SerializerDoesNotExist: Not yet implemented.
    """

    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist(
            "collection_manifest is a serialization-only serializer"
        )
