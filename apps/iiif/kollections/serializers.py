from .models import Collection
from apps.iiif.manifests.models import Manifest
from rest_framework import serializers
import json


class CollectionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Collection
        fields = ('metadata',)
