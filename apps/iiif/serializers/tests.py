"""Test Module for IIIF Serializers"""
from django.test import TestCase
from django.core.serializers import serialize, deserialize, SerializerDoesNotExist
from apps.iiif.canvases.models import Canvas

class SerializerTests(TestCase):
    serializers = [
        'annotation_list', 'annotation', 'canvas',
        'collection_manifest', 'kollection',
        'manifest', 'user_annotation_list'
    ]

    fixtures = [
        'users.json',
        'kollections.json',
        'manifests.json',
        'canvases.json',
        'annotations.json'
    ]


    def test_deserialization(self):
        """Deserialization should raise for serialization only error."""
        for serializer in self.serializers:
            try:
                deserialize(serializer, {})
            except SerializerDoesNotExist as error:
                assert str(error) == "'{s} is a serialization-only serializer'".format(s=serializer)

    def test_empty_object(self):
        """If specified version is not implemented, serializer returns an empty dict."""
        for serializer in self.serializers:
            obj = serialize(
                serializer,
                Canvas.objects.all(),
                version='Some Random Version'
            )
            assert 'null' in obj
