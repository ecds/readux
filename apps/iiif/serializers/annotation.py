from django.core.serializers.base import SerializerDoesNotExist
from django.core.serializers.json import Serializer as JSONSerializer
from apps.readux.models import UserAnnotation
import config.settings.local as settings

class Serializer(JSONSerializer):
    """
    Serialize a :class:`apps.iiif.annotation.models.Annotation` object based on the IIIF Presentation API

    IIIF V2 Annotation List https://iiif.io/api/presentation/2.1/#annotation-list
    """
    def _init_options(self):
        """
        Initialize object with options
        """        
        super()._init_options()
        self.version = self.json_kwargs.pop('version', 'v2')
        self.is_list = self.json_kwargs.pop('is_list', False)
        self.owners = self.json_kwargs.pop('owners', 0)

    def start_serialization(self):
        """
        Initialize the object and set the first character depending
        on if we are serailizing a single object or a list of objects.
        """
        self._init_options()
        if (self.is_list):
          self.stream.write('[')
        else:
          self.stream.write('')

    def end_serialization(self):
        """
        Set the last character depending on if we are serailizing a
        single object or a list of objects.
        """        
        if (self.is_list):
          self.stream.write(']')
        else:
          self.stream.write('')

    def start_object(self, obj):
        super().start_object(obj)

    def get_dump_object(self, obj):
        """
        Serialize an :class:`apps.iiif.annotation.models.Annotation`
        based on the IIIF presentation API
        
        :param obj: Annotation to be serialized.
        :type obj: :class:`apps.iiif.annotation.models.Annotation`
        :return: Serialzed annotation.
        :rtype: dict
        """        
        if ((self.version == 'v2') or (self.version is None)):
            name = 'OCR'
            if obj.owner_id:
                name = obj.owner.username if  "" == obj.owner.name else obj.owner.name
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": str(obj.pk),
                "@type": "oa:Annotation",
                "motivation": obj.motivation,
                "annotatedBy": {
                    "name": name
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
            if hasattr(obj, 'style') and obj.style is not None:
                data['stylesheet'] = self.__serialize_style(obj)

            if obj.item is not None:
                data['on']['selector']['item'] = self.__serialize_item(obj)
            else:
                data['on']['selector']['item'] = {'@type': 'oa:FragmentSelector'}

            if hasattr(obj, 'tags') and obj.tags.exists():
                data['motivation'] = data['motivation'].split(',')
                data['resource'] = [data['resource']]
                for tag in obj.tags.all():
                    wa_tag = {
                        "@type": "oa:Tag",
                        "chars": tag.name
                    }
                    data['resource'].append(wa_tag)

            return data

        elif (self.version == 'v3'):
            # TODO: write serializer for v3 of the IIIF Presentation API.
            return None

    def handle_field(self, obj, field):
        super().handle_field(obj, field)

    # TODO: is this needed?
    @classmethod
    def __serialize_item(self, obj):
        return obj.item
    
    @classmethod
    def __serialize_style(self, obj):
        """
        Serialize the stylesheet data.
        
        :param obj: Annotation to be serialized
        :type obj: :class:`apps.iiif.annotation.models.Annotation`
        :return: Stylesheet data compliant with the web annotation standard.
        :rtype: dict
        """        
        return {
            "type": "CssStylesheet",
            "value": obj.style
        }

class Deserializer:
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("annotation is a serialization-only serializer")