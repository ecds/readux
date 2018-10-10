from readux.annotations.models import Annotation
from rest_framework import serializers


class AnnotationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Annotation
        fields = ('iiif_annotation',)
