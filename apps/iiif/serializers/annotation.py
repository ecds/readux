from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers.json import Serializer as JSONSerializer
import config.settings.local as settings

class Serializer(JSONSerializer):
    """
    IIIF V2 Annotation List https://iiif.io/api/presentation/2.1/#annotation-list
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
                "@id": str(obj.pk),
                "@type": "oa:Annotation",
                "motivation": obj.motivation,
                "annotatedBy": {
                    "name": 'Me'
                },
                "resource": {
                    "@type": obj.resource_type,
                    "format": "text/html",
                    "chars": obj.content,
                    "language": obj.language
                },
                "on": {
                    "full": "%s/iiif/%s/%s/canvas/%s" % (settings.HOSTNAME, self.version, obj.canvas.manifest.pid, obj.canvas.pid),
                    "@type": "oa:SpecificResource",
                    "within": {
                        "@id": "%s/iiif/%s/%s/manifest" % (settings.HOSTNAME, self.version, obj.canvas.manifest.pid),
                        "@type": "sc:Manifest"
                    },
                    "selector": {
                        "@type": "oa:FragmentSelector",
                        "value": "xywh=%s,%s,%s,%s" % (str(obj.x), str(obj.y), str(obj.w), str(obj.h))
                    }
                }
            }
            return data

    def handle_field(self, obj, field):
        super().handle_field(obj, field)


class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("geojson is a serialization-only serializer")