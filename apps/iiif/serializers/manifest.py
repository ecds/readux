# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation Lists"""
import json
from datetime import datetime
from django.core.serializers import serialize, deserialize
from apps.iiif.canvases.models import Canvas
from apps.iiif.serializers.base import Serializer as JSONSerializer


class Serializer(JSONSerializer):
    """
    Convert a queryset to IIIF Manifest
    """

    def _init_options(self):
        super()._init_options()
        self.annotators = self.json_kwargs.pop("annotators", 0)
        # if 'exportdate' in self.json_kwargs:
        self.exportdate = self.json_kwargs.pop("exportdate", datetime.utcnow())
        self.current_user = self.json_kwargs.pop("current_user", None)
        # else:
        #      self.exportdate =

    def start_serialization(self):
        self._init_options()
        self.stream.write("")

    def end_serialization(self):
        self.stream.write("")

    def serialize_metadata(self, obj):
        """Convert metadata on object into list of {label, value} dicts"""
        if isinstance(obj.metadata, list):
            # most common case: metadata is already a list of {label, value} dicts
            return obj.metadata
        elif isinstance(obj.metadata, dict):
            # convert dict into list of label/value pair dicts
            return [{"label": key, "value": val} for (key, val) in obj.metadata.items()]
        else:
            return []

    def get_dump_object(self, obj):
        # TODO: Raise error if version is not v2 or v3
        if self.version == "v2" or self.version is None:
            within = []
            for col in obj.collections.all():
                within.append(col.get_absolute_url())
            try:
                thumbnail = "{h}/{p}".format(
                    h=obj.image_server.server_base, p=obj.start_canvas.resource
                )
            except (Canvas.MultipleObjectsReturned, Canvas.DoesNotExist):
                thumbnail = "{h}/{p}".format(
                    h=obj.image_server.server_base,
                    p=obj.canvas_set.all().first().resource,
                )

            if obj.metadata == {}:
                obj.metadata = None

            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": f"{obj.v2_baseurl}/manifest",
                "@type": "sc:Manifest",
                "label": obj.label,
                "metadata": [
                    {"label": "Author", "value": obj.author},
                    {"label": "Publisher", "value": obj.publisher},
                    {"label": "Place of Publication", "value": obj.published_city},
                    {"label": "Publication Date", "value": obj.published_date},
                    {"label": "Record Created", "value": obj.created_at},
                    {"label": "Edition Type", "value": "Readux IIIF Exported Edition"},
                    {
                        "label": "About Readux",
                        "value": "https://readux.ecdsdev.org/about/",
                    },
                    {"label": "Annotators", "value": self.annotators},
                    {"label": "Export Date", "value": self.exportdate},
                    # unpack serialized metadata (list of label, value pairs)
                    *self.serialize_metadata(obj),
                ],
                "description": obj.summary,
                "related": obj.related_links,
                "within": within,
                "thumbnail": {
                    "@id": thumbnail + "/full/600,/0/default.jpg",
                    "service": {
                        "@context": "http://iiif.io/api/image/2/context.json",
                        "@id": thumbnail,
                        "profile": "http://iiif.io/api/image/2/level1.json",
                    },
                },
                "attribution": obj.attribution,
                "logo": obj.logo_url or (obj.logo.url if obj.logo else ""),
                "license": obj.license,
                "viewingDirection": obj.viewingdirection,
                "viewingHint": "paged",
                "sequences": [
                    {
                        "@id": "%s/sequence/normal" % (obj.baseurl),
                        "@type": "sc:Sequence",
                        "label": "Current Page Order",
                        "startCanvas": obj.start_canvas.identifier,
                        "canvases": json.loads(
                            serialize(
                                "canvas",
                                obj.canvas_set.all(),
                                is_list=True,
                                current_user=self.current_user,
                            )
                        ),
                    }
                ],
                "seeAlso": obj.see_also_links,
            }
            return data
        return None


def Deserializer(data):
    """Deserialize IIIF Manifest"""

    if isinstance(data, str):
        data = json.loads(data)

    if "@context" in data and "2/context.json" in data["@context"]:
        return deserialize("manifest_v2", data)

    return deserialize("manifest_v3", data)
