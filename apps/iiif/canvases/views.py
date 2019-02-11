from rest_framework.generics import RetrieveAPIView, ListAPIView
# from rest_framework.schemas import ManualSchema
from django.http import JsonResponse
from django.views import View
from django.core.serializers import serialize
from .models import Canvas
from ..annotations.models import Annotation
from ..manifests.models import Manifest
# from .serializers import CanvasSerializer
import json
import uuid

class IIIFV2List(View):
    def get_queryset(self):
        return Canvas.objects.filter(manifest=Manifest.objects.get(pid=self.kwargs['manifest']))

    def get(self, request, *args, **kwargs):
        return JsonResponse(json.loads(serialize('canvas', self.get_queryset(), islist=True)), safe=False)

class IIIFV2Detail(View):
    def get_queryset(self):
        return Canvas.objects.filter(pid=self.kwargs['pid'])
    
    def get(self, request, *args, **kwargs):
        return JsonResponse(json.loads(serialize('canvas', self.get_queryset())))

class CreateAnnotation(View):
    def post(self, request, *args, **kwargs):
        # new_annotation = Annotation()
        # new_annotation.canvas = self.get_queryset()
        payload = json.loads(request.body)
        oa_annotation = json.loads(payload['oa_annotation'])
        canvas = Canvas.objects.get(pid=oa_annotation['on'][0]['full'].split('/')[-1])
        annotation = Annotation()
        annotation.canvas = canvas
        annotation.oa_annotation = oa_annotation
        annotation.save()
        return JsonResponse(oa_annotation, safe=False)