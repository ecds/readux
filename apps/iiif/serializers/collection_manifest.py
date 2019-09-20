from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers.json import Serializer as JSONSerializer
import config.settings.local as settings

class Serializer(JSONSerializer):
    """
    """
    def _init_options(self):
        super()._init_options()
        self.version = self.json_kwargs.pop('version', 'v2')
        self.is_list = self.json_kwargs.pop('is_list', False)

    def start_serialization(self):
        self._init_options()
        if (self.is_list):
          self.stream.write('[')
        else:
          self.stream.write('')

    def end_serialization(self):
        if (self.is_list):
          self.stream.write(']')
        else:
          self.stream.write('')

    def start_object(self, obj):
        super().start_object(obj)

    def get_dump_object(self, obj):
        if ((self.version == 'v2') or (self.version is None)):
            data =  {
              "@id": "%s/iiif/%s/manifest" % (settings.HOSTNAME, obj.pid),
              "@type": "sc:Manifest",
              "label": obj.label,
            }
            return data

    def handle_field(self, obj, field):
        super().handle_field(obj, field)


class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("geojson is a serialization-only serializer")