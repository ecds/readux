# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation Lists"""
import json
from datetime import datetime
from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers import serialize
from apps.iiif.canvases.models import Canvas
from apps.iiif.serializers.base import Serializer as JSONSerializer

class Serializer(JSONSerializer):
    """
    Convert a queryset to IIIF Manifest
    """
    def _init_options(self):
        super()._init_options()
        self.annotators = self.json_kwargs.pop('annotators', 0)
        # if 'exportdate' in self.json_kwargs:
        self.exportdate = self.json_kwargs.pop('exportdate', datetime.utcnow())
        # else:
        #      self.exportdate =

    def start_serialization(self):
        self._init_options()
        self.stream.write('')

    def end_serialization(self):
        self.stream.write('')

    def get_dump_object(self, obj):
        # TODO: Raise error if version is not v2 or v3
        if self.version == 'v2' or self.version is None:
            within = []
            for col in obj.collections.all():
                within.append(col.get_absolute_url())
            try:
                thumbnail = '{h}/{p}'.format(
                    h=obj.canvas_set.all().first().IIIF_IMAGE_SERVER_BASE,
                    p=obj.canvas_set.all().get(is_starting_page=True).pid
                )
            except (Canvas.MultipleObjectsReturned, Canvas.DoesNotExist):
                thumbnail = '{h}/{p}'.format(
                    h=obj.canvas_set.all().first().IIIF_IMAGE_SERVER_BASE,
                    p=obj.canvas_set.all().first().pid
                )

            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": "%s/manifest" % (obj.baseurl),
                "@type": "sc:Manifest",
                "label": obj.label,
                "metadata": [
                    {
                        "label": "Author",
                        "value": obj.author
                    },
                    {
                        "label": "Publisher",
                        "value": obj.publisher
                    },
                    {
                        "label": "Place of Publication",
                        "value": obj.published_city
                    },
                    {
                        "label": "Publication Date",
                        "value": obj.published_date
                    },
                    {
                        "label": "Notes",
                        "value": obj.metadata
                    },
                    {
                        "label": "Record Created",
                        "value": obj.created_at
                    },
                    {
                        "label": "Edition Type",
                        "value": "Readux IIIF Exported Edition"
                    },
                    {
                        "label": "About Readux",
                        "value": "https://readux.ecdsdev.org/about/"
                    },
                    {
                        "label": "Annotators",
                        "value": self.annotators
                    },
                    {
                        "label": "Export Date",
                        "value": self.exportdate
                    }
                ],
                "description": obj.summary,
                "related": [obj.get_volume_url()],
                "within": within,
                "thumbnail": {
                    "@id": thumbnail + "/full/600,/0/default.jpg",
                    "service": {
                        "@context": "http://iiif.io/api/image/2/context.json",
                        "@id": thumbnail,
                        "profile": "http://iiif.io/api/image/2/level1.json"
                    }
                },
                "attribution": obj.attribution,
                "logo": obj.thumbnail_logo,
                "license": obj.license,
                "viewingDirection": obj.viewingDirection,
                "viewingHint": "paged",
                "sequences": [
                    {
                        "@id": "%s/sequence/normal" % (obj.baseurl),
                        "@type": "sc:Sequence",
                        "label": "Current Page Order",
                        "startCanvas": obj.start_canvas,
                        "canvases": json.loads(
                            serialize(
                                'canvas',
                                obj.canvas_set.all(),
                                is_list=True
                            )
                        )
                    }
                ]
            }
            return data
        return None

class Deserializer:
    """Deserialize IIIF Annotation List

    :raises SerializerDoesNotExist: Not yet implemented.
    """
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("manifest is a serialization-only serializer")
