from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers.json import Serializer as JSONSerializer
from django.core.serializers import serialize
import json

"""
V2
{
  // Metadata about this canvas
  "@context": "https://iiif.io/api/presentation/2/context.json",
  "@id": 'https://example.org/iiif/%s/canvas/p1' % (obj.pid),
  "@type": "sc:Canvas",
  "label": "p. 1",
  "height": 1000,
  "width": 750,
  "thumbnail" : {
    "@id" : "https://example.org/iiif/book1/canvas/p1/thumb.jpg",
    "@type": "dctypes:Image",
    "height": 200,
    "width": 150
  },
  "images": [
    {
      "@type": "oa:Annotation"
      // Link from Image to canvas should be included here, as below
    }
  ],
  "otherContent": [
    {
      // Reference to list of other Content resources, _not included directly_
      "@id": "https://example.org/iiif/book1/list/p1",
      "@type": "sc:AnnotationList"
    }
  ]

}

V3
{
  // Metadata about this canvas
  "id": "https://example.org/iiif/book1/canvas/p1",
  "type": "Canvas",
  "label": { "@none": [ "p. 1" ] },
  "height": 1000,
  "width": 750,

  "items": [
    {
      "id": "https://example.org/iiif/book1/page/p1/1",
      "type": "AnnotationPage",
      "items": [
        // Content Annotations on the Canvas are included here
      ]
    }
  ]
}
"""

class Serializer(JSONSerializer):
    """
    Convert a queryset to GeoJSON, https://geojson.org/
    """
    def _init_options(self):
        super()._init_options()
        self.version = self.json_kwargs.pop('version', 'v2')

    def start_serialization(self):
        self._init_options()
        self.stream.write('')

    def end_serialization(self):
        self.stream.write('')

    def start_object(self, obj):
        super().start_object(obj)

    def get_dump_object(self, obj):
        if ((self.version == 'v2') or (self.version is None)):
            data = {
              "@context": "https://iiif.io/api/presentation/2/context.json",
              "@id": "https://example.org/iiif/%s/manifest" % (obj.pid),
              "@type": "sc:Manifest",
              "label": obj.label,
              "metadata": [{
                "label": "Author",
                "value": obj.author
              },
              {
                "label": "Published",
                "value": [{
                    "@value": "%s : %s, %s" %(obj.published_city, obj.publisher, obj.published_date),
                    "@language": "en"
                  }
                ]
              },
              {
                "label": "Notes",
                "value": [obj.note_set.values('label')[0]['label']]
              }],
              "sequences": [
                {
                  "@id": "https://example.org/iiif/book1/sequence/normal",
                  "@type": "sc:Sequence",
                  "label": "Current Page Order",
                  "viewingDirection": obj.viewingDirection,
                  "viewingHint": "paged",
                  "startCanvas": "https://example.org/iiif/book1/canvas/p2",
                  "canvases": json.loads(serialize('canvas', obj.canvas_set.all(), islist=True))
                }
              ]
            }
            return data

    def handle_field(self, obj, field):
        super().handle_field(obj, field)


class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("geojson is a serialization-only serializer")