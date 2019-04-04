from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers.json import Serializer as JSONSerializer
import config.settings.local as settings
from django.core.serializers import serialize
import json

class Serializer(JSONSerializer):
    """
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
              "@context": "https://iiif.io/api/presentation/2/context.json",
              "@id": "https://example.org/iiif/v2/%s/collection" % (obj.pid),
              "@type": "sc:Collection",
              "label": obj.label,
              "viewingHint": "top",
              "description": obj.summary,
              "attribution": obj.attribution,
              "manifests": json.loads(serialize('collection_manifest', obj.manifests.all(), islist=True))
            }
            return data

    def handle_field(self, obj, field):
        super().handle_field(obj, field)


class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("geojson is a serialization-only serializer")