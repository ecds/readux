"""Django views for :class:`apps.iiif.annotations`"""
import json
from django.views import View
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from ..canvases.models import Canvas
from .models import Annotation

USER = get_user_model()
class AnnotationsForPage(View):
    """
    Endpoint to to display annotations for a page.
    """
    def get_queryset(self):
        """
        Function to get `.models.Annotation` objects for a given `..canvases.models.Canvas`.
        Canvas objects is found by the `canvas.pid` found with the 'page' key in the requests
        key word arguments (kwargs).
        """
        canvas = Canvas.objects.get(pid=self.kwargs['page'])
        return Annotation.objects.filter(canvas=canvas).distinct('order')
    
    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """
        Function to respond to HTTP GET requests for annotations for a given canvas.

        :param request: HTTP GET request
        :type request: django request object?
        :return: Serialized JSON based on the IIIF presentation API standads.
        :rtype: JSON
        """
        # TODO: Does this view need owners?
        # owners = [request.user.id]
        return JsonResponse(
            json.loads(
                serialize(
                    'annotation',
                    self.get_queryset(),
                    is_list=True
                )
            ),
            safe=False
        )

class OcrForPage(View):
    """
    Django View for getting OCR annotations for a given canvas.
    """
    def get_queryset(self):
        """
        Function to get `.models.Annotation` objects for a given `..canvases.models.Canvas`.
        Canvas objects is found by the `canvas.pid` found with the 'page' key in the requests
        key word arguments (kwargs).

        :return: OCR annotations for given canvas.
        :rtype: Django QuerySet
        """
        return Canvas.objects.filter(pid=self.kwargs['page'])

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """
        Function to respond to HTTP GET requests for ocr annotations for a given canvas.

        :param request: HTTP GET request
        :type request: django request object?
        :return: Serialized JSON based on the IIIF presentation API standads.
        :rtype: JSON
        """
        owners = [USER.objects.get(username='ocr', name='OCR')]

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
