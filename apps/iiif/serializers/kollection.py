# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation Lists"""
import json
from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers import serialize
import config.settings.local as settings
from apps.iiif.serializers.base import Serializer as JSONSerializer


class Serializer(JSONSerializer):
    """
    IIIF Collection
    """

    def get_dump_object(self, obj):
        if (self.version == "v2") or (self.version is None):
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": "{h}/iiif/{v}/{p}/collection".format(
                    h=settings.HOSTNAME, v=self.version, p=obj.pid
                ),
                "@type": "sc:Collection",
                "label": obj.label,
                "viewingHint": "top",
                "description": obj.summary,
                "attribution": obj.attribution,
                "manifests": json.loads(
                    serialize("collection_manifest", obj.manifests.all(), is_list=True)
                ),
            }
            return data
        return None


class Deserializer:
    """Deserialize IIIF Annotation List

    :raises SerializerDoesNotExist: Not yet implemented.
    """

    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("kollection is a serialization-only serializer")
