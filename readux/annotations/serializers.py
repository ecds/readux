from readux.annotations.models import Annotation
from rest_framework import serializers
class AnnotationSerializer(serializers.HyperlinkedModelSerializer):
    oa_annotation = serializers.SerializerMethodField('clean_json')

    class Meta:
        model = Annotation
        fields = ('iiif_annotation', 'oa_annotation')
    
    def clean_json(self, obj):
        return obj.iiif_annotation

class AnnotationPostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Annotation
        fields = ('iiif_annotation',)