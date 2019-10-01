from rest_framework import generics
from django.views import View
from django.views.generic import ListView
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
import json
from django.http import JsonResponse
from .models import Annotation
from ..canvases.models import Canvas

User = get_user_model()
class AnnotationsForPage(View):
    """
    Endpoint to to display annotations for a page.
    """

    def get_queryset(self):
        canvas = Canvas.objects.get(pid=self.kwargs['page'])
        return Annotation.objects.filter(canvas=canvas).distinct('order')
    
    def get(self, request, *args, **kwargs):
        # TODO Does this view need owners?
        # owners = [request.user.id]
        return JsonResponse(
            json.loads(
                serialize(
                    'annotation',
                    self.get_queryset(),
                    # version=kwargs['version'],
                    # owners=owners,
                    is_list = True
                )
            ),
            safe=False
        )


# class AnnotationDetail(generics.RetrieveUpdateDestroyAPIView):
#     """
#     Endpoint to update and delete annotation.
#     """
#     serializer_class = AnnotationSerialize

#     def get_queryset(self):
#         return Annotation.objects.all()

class OcrForPage(View):
    def get_queryset(self):
        return Canvas.objects.filter(pid=self.kwargs['page'])
    
    def get(self, request, *args, **kwargs):
        owners = [User.objects.get(username='ocr', name='OCR')]

        return JsonResponse(
            json.loads(
                serialize(
                    'annotation_list',
                    self.get_queryset(),
                    version=kwargs['version'],
                    owners=owners
                )
            ),
            safe=False
        )
