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
        self.islist = self.json_kwargs.pop('islist', False)
        self.owners = self.json_kwargs.pop('owners')

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
                "@id": "%s/iiif/v2/%s/list/%s" % (settings.HOSTNAME, obj.manifest.pid, obj.pid),
                "@type": "sc:AnnotationList",
                "resources": json.loads(serialize('annotation', obj.annotation_set.filter(Q(owner=None) | Q(owner__in=self.owners)), islist=True))
            }
            return data

    def handle_field(self, obj, field):
        super().handle_field(obj, field)


class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("geojson is a serialization-only serializer")