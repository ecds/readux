from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Manifest
from apps.iiif.annotations.models import Annotation
import json
import os.path
import tempfile

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

    def get(self, request, *args, **kwargs):
        # we should probably move this out of the view, into a library
        manifest = self.get_queryset()[0]
        tmpdir = tempfile.mkdtemp()
        outdir = os.path.join(tmpdir, manifest.label)
        zip_path = os.path.join(tmpdir, "iiif_export.zip")
        os.mkdir(outdir)

        manifest_path = os.path.join(outdir, "manifest.json")
        with open(manifest_path, "w") as manifest_file:
            manifest_file.write(
                serialize(
                    'manifest',
                    self.get_queryset(),
                    version=kwargs['version']
                )
            )

        written_filenames = []
        for canvas in manifest.canvas_set.all():
            annotations_path = os.path.join(outdir, canvas.pid) # we cannot use the IRI for the annotation list because of invalid characters in the filename
            with open(annotations_path, "w") as annotations_file:
                annotations_file.write(
                    serialize(
                        'annotation_list',
                        [canvas],
                        version=kwargs['version']
                    )
                )

#        finally:
            # Remove our temporary directory
#            shutil.rmtree(tmpdir, ignore_errors=True)
        

        return JsonResponse({'success': 'not implemented yet'})
