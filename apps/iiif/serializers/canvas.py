# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Canvas"""
from django.core.serializers.base import SerializerDoesNotExist
from django.urls import reverse
from django.contrib.auth import get_user_model
import config.settings.local as settings
from apps.iiif.serializers.base import Serializer as JSONSerializer

USER = get_user_model()

class Serializer(JSONSerializer):
    """
    Convert a queryset to IIIF Canvas
    """
    def _init_options(self):
        super()._init_options()
        self.current_user = self.json_kwargs.pop('current_user', None)

    def get_dump_object(self, obj):
        obj.label = str(obj.position)
        if ((self.version == 'v2') or (self.version is None)):
            otherContent = [ # pylint: disable=invalid-name
                {
                    "@id": '{m}/list/{c}'.format(m=obj.manifest.baseurl, c=obj.pid),
                    "@type": "sc:AnnotationList",
                    "label": "OCR Text"
                }
            ]
            #
            # Only list annotation lists for current user. I'm going to leave the code below
            # for when eventually implement groups.
            #
            # for user in USER.objects.filter(userannotation__canvas=obj).distinct():
            #     kwargs = {
            #       'username': user.username,
            #       'volume': obj.manifest.pid,
            #       'canvas': obj.pid
            #     }
            #     url = "{h}{k}".format(
            #         h=settings.HOSTNAME,
            #         k=reverse('user_annotations', kwargs=kwargs)
            #     )
            #     user_endpoint = {
            #         "label": 'Annotations by {u}'.format(u=user.username),
            #         "@type": "sc:AnnotationList",
            #         "@id": url
            #     }
            #     otherContent.append(user_endpoint)
            current_user_has_annotations = (
                self.current_user
                and self.current_user.is_authenticated
                and self.current_user.userannotation_set.filter(canvas=obj).exists()
            )
            if current_user_has_annotations:
                kwargs = {
                    'username': self.current_user.username,
                    'volume': obj.manifest.pid,
                    'canvas': obj.pid
                }
                url = "{h}{k}".format(
                    h=settings.HOSTNAME,
                    k=reverse('user_annotations', kwargs=kwargs)
                )
                otherContent.append(
                    {
                        "label": 'Annotations by {u}'.format(u=self.current_user.username),
                        "@type": "sc:AnnotationList",
                        "@id": url
                    }
                )
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
                        "@id": str(obj.anno_id),
                        "@type": "oa:Annotation",
                        "motivation": "sc:painting",
                        "resource": {
                            "@id": '{id}/full/full/0/default.jpg'.format(id=obj.resource_id),
                            "@type": "dctypes:Image",
                            "format": "image/jpeg",
                            "height": obj.height,
                            "width": obj.width,
                            "service": {
                                "@context": "https://iiif.io/api/image/2/context.json",
                                "@id": obj.resource_id,
                                "profile": "https://iiif.io/api/image/2/level2.json"
                            }
                        },
                        "on": obj.identifier,
                    }
                ],
                "thumbnail" : {
                    "@id" : obj.thumbnail,
                    "height": 250,
                    "width": 200
                },
                "otherContent" : otherContent
            }
            return data
        # TODO: Should probably return a helpful error.
        return None

class Deserializer:
    """Deserialize IIIF Annotation List

    :raises SerializerDoesNotExist: Not yet implemented.
    """
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("canvas is a serialization-only serializer")
