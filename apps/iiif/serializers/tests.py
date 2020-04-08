from django.test import TestCase
from django.core.serializers import serialize, deserialize, SerializerDoesNotExist

class SerializerTests(TestCase):
    serializers = ['annotation_list', 'annotation', 'canvas', 'collection_manifest', 'kollection', 'manifest', 'user_annotation_list']

    def test_deserialization(self):
        for serializer in self.serializers:
            try:
                deserialize(serializer, {})
            except SerializerDoesNotExist as error:
                assert str(error) == "'{s} is a serialization-only serializer'".format(s=serializer)
