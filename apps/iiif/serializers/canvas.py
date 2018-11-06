from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers.json import Serializer as JSONSerializer

"""
V2
{
  // Metadata about this canvas
  "@context": "http://iiif.io/api/presentation/2/context.json",
  "@id": "http://example.org/iiif/book1/canvas/p1",
  "@type": "sc:Canvas",
  "label": "p. 1",
  "height": 1000,
  "width": 750,
  "thumbnail" : {
    "@id" : "http://example.org/iiif/book1/canvas/p1/thumb.jpg",
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
      "@id": "http://example.org/iiif/book1/list/p1",
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
    Convert a queryset to GeoJSON, http://geojson.org/
    """
    def _init_options(self):
        super()._init_options()
        self.version = self.json_kwargs.pop('version', 'v2')
        self.islist = self.json_kwargs.pop('islist', False)

    def start_serialization(self):
        self._init_options()
        if (self.islist):
          self.stream.write('[')
        else:
          self.stream.write('')

    def end_serialization(self):
        if (self.islist):
          self.stream.write(']')
        else:
          self.stream.write('')

    def start_object(self, obj):
        super().start_object(obj)

    def get_dump_object(self, obj):
        if ((self.version == 'v2') or (self.version is None)):
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": obj.identifier,
                "@type": "sc:Canvas",
                "label": obj.label,
                "height": obj.height,
                "width": obj.width,
                "images": [
                  {
                    "@context": "http://iiif.io/api/presentation/2/context.json",
                    "@id": "http://example.org/iiif/book1/annotation/p0001-image",
                    "@type": "oa:Annotation",
                    "motivation": "sc:painting",
                    "resource": {
                      "@id": "http://loris.library.emory.edu/%s/full/full/0/default.jpg" % (obj.pid),
                      "@type": "dctypes:Image",
                      "format": "image/jpeg",
                      "height": obj.height,
                      "width": obj.width,
                      "service": {
                        "@context": "http://iiif.io/api/image/2/context.json",
                        "@id": obj.service_id,
                        "profile": "http://iiif.io/api/image/2/level2.json"
                      }
                    },
                    "on": "http://example.org/iiif/book1/canvas/p1"
                  }
                ],
                "thumbnail" : {
                    "@id" : obj.thumbnail,
                    "@type": "dctypes:Image",
                    "height": 250,
                    "width": 200
                }
            }
            return data

    def handle_field(self, obj, field):
        super().handle_field(obj, field)


class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("geojson is a serialization-only serializer")