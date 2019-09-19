from rest_framework import generics
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Collection
from apps.iiif.manifests.models import Manifest
import json

# TODO Would still be nice to use DRF. Try this?
# https://stackoverflow.com/a/35019122

# TODO is this view needed?
class ManifestsForCollection(View):
    """
    Endpoint to to display list of manifests for a given collection.
    """

    def get_queryset(self):
        collection = Collection.objects.get(pid=self.kwargs['pid'])
        return Manifest.objects.filter(collections=collection)

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            json.loads(
                serialize(
                    'collection_manifest',
                    self.get_queryset(),
                    # version=kwargs['version'],
                    is_list = True
                )
            ),
            safe=False
        )

class CollectionDetail(View):
    """
    Endpoint to display serialized IIIF collection
    """

    def get_queryset(self):
        return Collection.objects.filter(pid=self.kwargs['pid'])

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            json.loads(
                serialize(
                    'kollection',
                    self.get_queryset(),
                    version=kwargs['version']
                )
            )
        , safe=False)


class CollectionSitemap(Sitemap):
    # priority unknown
    def items(self):
        return Collection.objects.all()

    def location(self, item):
        return reverse('CollectionRender', kwargs={'version': 'v2', 'pid': item.pid})
