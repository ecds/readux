from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Manifest
import json

# TODO Would still be nice to use DRF. Try this?
# https://stackoverflow.com/a/35019122
class ManifestDetail(View):

    def get_queryset(self):
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            json.loads(
                serialize(
                    'manifest',
                    self.get_queryset(),
                    version=kwargs['version']
                )
            )
        , safe=False)

class ManifestSitemap(Sitemap):
    # priority unknown
    def items(self):
        return Manifest.objects.all()

    def location(self, item):
        return reverse('ManifestRender', kwargs={'version': 'v2', 'pid': item.pid})
