"""Django views for Kollections"""
import json
from django.http import JsonResponse
from django.views import View
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Collection
from ..manifests.models import Manifest

class ManifestsForCollection(View):
    """
    Endpoint to to display list of manifests for a given collection.
    """

    def get_queryset(self):
        """Get all manifests for a requested collection.

        :return: Canvases belonging to requested manifest.
        :rtype: django.db.models.query.QuerySet
        """
        collection = Collection.objects.get(pid=self.kwargs['pid'])
        return Manifest.objects.filter(collections=collection)

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """HTTP GET endpoint responds with IIIF v2 presentation API representation of a collection.

        :return: IIIF v2 presentation API collection
        :rtype: JSON
        """
        return JsonResponse(
            json.loads(
                serialize(
                    'collection_manifest',
                    self.get_queryset(),
                    # version=kwargs['version'],
                    is_list=True
                )
            ),
            safe=False
        )

class CollectionDetail(View):
    """
    Endpoint to display serialized IIIF collection
    """

    def get_queryset(self):
        """Get specific collection.

        :return: Canvas object.
        :rtype: django.db.models.query.QuerySet
        """
        return Collection.objects.filter(pid=self.kwargs['pid'])

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """HTTP GET endpoint responds with IIIF v2 presentation API representation of a collection.

        :return: IIIF v2 presentation API collection
        :rtype: JSON
        """
        return JsonResponse(
            json.loads(
                serialize(
                    'kollection',
                    self.get_queryset(),
                    version=kwargs['version']
                )
            ),
            safe=False)


class CollectionSitemap(Sitemap):
    """Django Sitemap for Kollection"""
    # priority unknown
    def items(self):
        return Collection.objects.all()

    def location(self, obj):
        return reverse('CollectionRender', kwargs={'version': 'v2', 'pid': obj.pid})
