"""
Django view for canvases
"""
import json
from django.http import JsonResponse
from django.views import View
from django.core.serializers import serialize
from .models import Canvas
from ..manifests.models import Manifest
# from .serializers import CanvasSerializer

class IIIFV2List(View):
    """Django view to list canvases according to the
    IIIF v2 presentation API.

    :return: IIIF v2 presentation API canvas list
    :rtype: JSON
    """
    def get_queryset(self):
        """Get all canvases for a requested manifest.

        :return: Canvases belonging to requested manifest.
        :rtype: django.db.models.query.QuerySet
        """
        return Canvas.objects.filter(manifest=Manifest.objects.get(pid=self.kwargs['manifest']))

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """HTTP GET endpoint responds with IIIF v2 presentation API of a canvas list.

        :return: IIIF v2 presentation API canvas list
        :rtype: JSON
        """
        return JsonResponse(
            json.loads(
                serialize(
                    'canvas',
                    self.get_queryset(),
                    is_list=True
                )
            ),
            safe=False
        )

class IIIFV2Detail(View):
    """Django view to represent specific canvases
    according to the IIIF v2 presentation API.

    :return: IIIF v2 presentation API canvas
    :rtype: JSON
    """

    def get_queryset(self):
        """Get all canvases for a requested canvas.

        :return: Specific canvas details.
        :rtype: django.db.models.query.QuerySet
        """
        return Canvas.objects.filter(pid=self.kwargs['pid'])

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """Responds to HTTP GET requests to endpoint with
        IIIF v2 presentation API a canvas.

        :return: IIIF v2 presentation API a canvas
        :rtype: JSON
        """
        return JsonResponse(
            json.loads(
                serialize(
                    'canvas',
                    self.get_queryset()
                )
            ),
            safe=False
        )
