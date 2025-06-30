"""Module for serializing IIIF V2 Canvas Lists"""

import re
from apps.iiif.serializers.canvas import Serializer as CanvasSerializer
from apps.iiif.manifests.models import Manifest


class Serializer(CanvasSerializer):
    """Convert a queryset to IIIF Canvas"""


def Deserializer(data):  # pylint: disable=invalid-name
    """Deserialize V2 Canvas.

    Args:
        data (dict): V2 IIIF Canvas

    Returns:
        dict: canvas dict
    """
    return {
        "pid": data["@id"].split("/")[-1],
        "resource": data["images"][0]["resource"]["service"]["@id"].split("/")[-1],
        "width": data["images"][0]["resource"]["width"],
        "height": data["images"][0]["resource"]["height"],
    }
