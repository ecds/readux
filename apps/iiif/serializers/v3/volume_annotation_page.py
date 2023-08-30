# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation Lists"""
import json
from django.core.serializers import serialize, deserialize
from django.core.serializers.base import SerializerDoesNotExist
from django.contrib.auth import get_user_model
from django.db.models import Q
import config.settings.local as settings
from ..base import Serializer as JSONSerializer

USER = get_user_model()

class Serializer(JSONSerializer):
    """
    IIIF V3 Annotation Page https://iiif.io/api/presentation/3.0/#55-annotation-page
    """
    def _init_options(self):
        super()._init_options()
        self.volume_annotations = self.json_kwargs.pop('volume_annotations', 0)

    def get_dump_object(self, obj):
        # TODO: Add more validation checks before trying to serialize.
        data = {
            '@context': 'http://iiif.io/api/presentation/3/context.json',
            'id': '{h}/iiif/{m}/annotationpage/{c}'.format(
                h=settings.HOSTNAME,
                m=obj.pid,
                c=obj.pid
            ),
            'type': 'AnnotationPage'
        }

        items = []

        for canvas_annotation in self.volume_annotations:
            for annotation in canvas_annotation:
                items.append(
                    json.loads(
                        serialize(
                            'annotation_v3',
                            [annotation]
                        )
                    )
                )

        data['items'] = items

        return data

def Deserializer(data):
    """Deserialize IIIF Annotation Page

    :returns list of Annotations.
    """
    annotations = []

    for item in data['items']:
        annotations.append(deserialize('annotation_v3', item))

    return annotations

