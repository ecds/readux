"""Module for serializing IIIF V2 Manifest Lists"""

import re
from apps.iiif.serializers.manifest import Serializer as ManifestSerializer
from apps.iiif.manifests.models import Manifest


class Serializer(ManifestSerializer):
    """Convert a queryset to IIIF Manifest"""


def parse_fields(attribute):
    """Get attributes from V2 Manifest

    Args:
        attribute (tuple): _description_
    """
    key, value = attribute
    fields = [field.name for field in Manifest._meta.get_fields()]
    field = re.sub(r"\([^)]*\)", "", key).strip()
    field = field.replace(" ", "_")
    field = field.lower()
    if field == "publication_date":
        return {"published_date": value}
    if field == "place_of_publication":
        return {"published_city": value}
    if field in fields:
        return {field: value}
    return None


def Deserializer(data):  # pylint: disable=invalid-name
    """Deserialize V2 Manifest.

    Args:
        data (dict): V2 IIIF Manifest

    Returns:
        tuple: manifest dict and relationships
    """
    relations = {
        "collections": data["within"],
        "related_links": data["seeAlso"],
        "canvases": [
            canvas["@id"].split("/")[-1] for canvas in data["sequences"][0]["canvases"]
        ],
    }

    manifest = {
        "pid": data["@id"].split("/")[-2],
        "summary": data["description"],
    }

    try:
        metadata = data.pop("metadata")
        for metadatum in metadata:
            attribute = parse_fields((metadatum["label"], metadatum["value"]))
            if attribute is not None:
                manifest = {**manifest, **attribute}
    except KeyError:
        # Maybe no metadata
        pass

    for key, value in data.items():
        attribute = parse_fields((key, value))
        if attribute is not None:
            data = {**data, **attribute}

    return (manifest, relations)
