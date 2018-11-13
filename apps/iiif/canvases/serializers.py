from .models import Canvas
from rest_framework import serializers
import json


class CanvasSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=200)
    pk = serializers.CharField(max_length=200)
