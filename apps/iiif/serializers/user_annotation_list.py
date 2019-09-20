from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers.json import Serializer as JSONSerializer
from django.db.models import Q
import config.settings.local as settings
from django.core.serializers import serialize
import json

class Serializer(JSONSerializer):
    """
    IIIF V2 Annotation List https://iiif.io/api/presentation/2.1/#annotation-list
    """
    def _init_options(self):
        super()._init_options()
        self.version = self.json_kwargs.pop('version', 'v2')
        self.is_list = self.json_kwargs.pop('is_list', False)
        self.owners = self.json_kwargs.pop('owners', 0)

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
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": "%s/annotations/%s/%s/%s/list" % (settings.HOSTNAME, self.owners[0].username, obj.manifest.pid, obj.pid),
                "@type": "sc:AnnotationList",
                "resources": json.loads(serialize('annotation', obj.userannotation_set.filter(owner__in=self.owners), is_list=True))
            }
            return data

    def handle_field(self, obj, field):
        super().handle_field(obj, field)


class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("geojson is a serialization-only serializer")