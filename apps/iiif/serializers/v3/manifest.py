"""Module for serializing IIIF Annotation Lists"""

import json
from django.core.serializers import serialize, deserialize
from apps.iiif.canvases.models import Canvas
from apps.iiif.serializers.base import Serializer as JSONSerializer


class Serializer(JSONSerializer):
    """
    Convert a queryset to IIIF Manifest
    """

    def _init_options(self):
        super()._init_options()
        self.current_user = self.json_kwargs.pop("current_user", None)

    def get_dump_object(self, obj):
        try:
            thumbnail = f"{obj.image_server.server_base}/{obj.start_canvas.resource}"
        except (Canvas.MultipleObjectsReturned, Canvas.DoesNotExist):
            thumbnail = f"{obj.image_server.server_base}/{obj.canvas_set.all().first().resource}"

        data = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": f"{obj.v3_baseurl}/manifest",
            "type": "Manifest",
            "label": obj.label,
            "metadata": obj.metadata,
            "summary": {"none": [obj.summary]},
            "thumbnail": [
                {
                    "id": f"{thumbnail}/full/600,/0/default.jpg",
                    "type": "Image",
                    "format": "image/jpeg",
                    "service": [
                        {"id": thumbnail, "type": "ImageService3", "profile": "level1"}
                    ],
                }
            ],
            "items": [],
        }

        for canvas in obj.canvas_set.all():
            data["items"].append(
                json.loads(
                    serialize("canvas_v3", [canvas], current_user=self.current_user)
                )
            )

        return data


# class Deserializer:
#     """
#     Deserialize IIIF v3 Manifest
#     """
