# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing all volumes manifest"""
from django.core.serializers.base import SerializerDoesNotExist
import config.settings.local as settings
from apps.iiif.serializers.base import Serializer as JSONSerializer

class Serializer(JSONSerializer):
    """Serializer for a single IIIF manifest within the Readux all-volumes collection"""

    def get_dump_object(self, obj):
        if ((self.version == 'v2') or (self.version is None)):
            data = {
                "@id": '{h}/iiif/v2/{p}/manifest'.format(h=settings.HOSTNAME, p=obj.pid),
                "@type": "sc:Manifest",
                "label": obj.label,
                "modified": obj.updated_at.isoformat(),
                "within": [{
                    "@id": '{h}/iiif/v2/{p}/collection'.format(h=settings.HOSTNAME, p=collection.pid),
                    "@type": "sc:Collection",
                    "label": collection.label
                } for collection in obj.collections.all()]
            }
            return data
        return None

class Deserializer:
    """Deserialize IIIF all volumes manifest

    :raises SerializerDoesNotExist: Not yet implemented.
    """
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("all_volumes_manifest is a serialization-only serializer")
