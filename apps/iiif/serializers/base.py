from django.core.serializers.json import Serializer as JSONSerializer

class Serializer(JSONSerializer):
    """Base Serializer Class"""
    def _init_options(self):
        super()._init_options()
        self.version = self.json_kwargs.pop('version', 'v2')
        self.is_list = self.json_kwargs.pop('is_list', False)

    def start_serialization(self):
        self._init_options()
        if self.is_list:
            self.stream.write('[')
        else:
            self.stream.write('')

    def end_serialization(self):
        if self.is_list:
            self.stream.write(']')
        else:
            self.stream.write('')