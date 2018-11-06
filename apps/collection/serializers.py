from .models import Collection
from rest_framework import serializers
import json

"""
{
  "@context": [
    "http://www.w3.org/ns/anno.jsonld",
    "http://iiif.io/api/presentation/3/context.json"
  ],
  "id": "https://example.org/iiif/collection/top",
  "type": "Collection",
  "label": { "en": [ "Collection for Example Organization" ] },
  "summary": { "en": [ "Short summary of the Collection" ] },
  "requiredStatement": {
    "label": { "en": [ "Attribution" ] },
    "value": { "en": [ "Provided by Example Organization" ] }
  },

  "items": [
    {
      "id": "https://example.org/iiif/1/manifest",
      "type": "Manifest",
      "label": { "en": "Example Manifest 1" },
      "thumbnail": [
        {
          "id": "https://example.org/manifest1/thumbnail.jpg",
          "type": "Image"
        }
      ]
    }
  ]
}
"""


class CollectionSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = Collection
        fields = ('iiif_annotation',)

    def to_representation(self, obj):
        primitive_repr = super(CollectionSerializer, self).to_representation(obj)
        primitive_repr['@label'] = primitive_repr['label']
        return primitive_repr
