from rest_framework import generics
from django.views import View
from django.core.serializers import serialize
import json
from django.http import JsonResponse
from .models import Annotation
from ..canvases.models import Canvas
from .serializers import AnnotationSerializer


class AnnotationListCreate(generics.ListCreateAPIView):
    """
    Endpoint that allows annotations to be listed or created.
    """
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer


class AnnotationsForPage(View):
    """
    Endpoint to to display annotations for a page.
    """
    # serializer_class = AnnotationSerializer

    def get_queryset(self):
        canvas = Canvas.objects.get(pid=self.kwargs['page'])
        return Annotation.objects.filter(canvas=canvas).distinct('order')
    
    def get(self, request, *args, **kwargs):
        return JsonResponse(
            json.loads(
                serialize(
                    'annotation',
                    self.get_queryset(),
                    # version=kwargs['version'],
                    islist = True
                )
            ),
            safe=False
        )


class AnnotationDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint to update and delete annotation.
    """
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        return Annotation.objects.all()

class OcrForPage(View):
    def get_queryset(self):
        return Canvas.objects.filter(pid=self.kwargs['page'])
    
    def get(self, request, *args, **kwargs):
        return JsonResponse(
            json.loads(
                serialize(
                    'annotation_list',
                    self.get_queryset(),
                    request=request,
                    version=kwargs['version']
                )
            ),
            safe=False
        )
