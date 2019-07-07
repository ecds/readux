from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Manifest
from .export import IiifManifestExport
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

class ManifestRis(TemplateView):
    content_type = 'application/x-research-info-systems; charset=UTF-8'
    template_name = "citation.ris"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context


class ManifestExport(View):

    def get_queryset(self):
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def post(self, request, *args, **kwargs):
        # we should probably move this out of the view, into a library
        manifest = self.get_queryset()[0]

        zip = IiifManifestExport.get_zip(manifest, kwargs['version'])
        resp = HttpResponse(zip, content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=iiif_export.zip'

        return resp

class JekyllExport(View):

    def get_queryset(self):
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def post(self, request, *args, **kwargs):
        # we should probably move this out of the view, into a library
        manifest = self.get_queryset()[0]

        zip = IiifManifestExport.get_zip(manifest, kwargs['version'])
        resp = HttpResponse(zip, content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=iiif_export.zip'

        return resp
