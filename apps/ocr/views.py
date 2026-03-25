"""Django views for :class:`apps.iiif.annotations`"""
import json
from django.views.generic import ListView
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from apps.iiif.canvases.models import Canvas

USER = get_user_model()

class WebAnnotationOCRForPage(ListView):
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
        return Canvas.objects.filter(pid=self.kwargs['canvas'])

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """
        Function to respond to HTTP GET requests for ocr annotations for a given canvas.

        :param request: HTTP GET request
        :type request: django request object?
        :return: Serialized JSON based on the IIIF presentation API standards.
        :rtype: JSON
        """
        owner = USER.objects.get(username='ocr', name='OCR')

        query_set = self.get_queryset()

        return JsonResponse(
            json.loads(
                serialize(
                    'annotation_page_v3',
                    query_set,
                    annotations=query_set.first().annotation_set.filter(owner=owner)
                )
            ),
            safe=False
        )
