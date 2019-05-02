from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Manifest
from apps.iiif.annotations.models import Annotation
import json
import zipfile
import io

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
        # tmpdir = tempfile.mkdtemp()
        # outdir = os.path.join(tmpdir, manifest.label)
        # os.mkdir(outdir)
        zip_subdir = manifest.label
        zip_filename = "iiif_export.zip"

        # Open StringIO to grab in-memory ZIP contents
        s = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        zf.writestr('test.txt', 'test contents')
        zf.writestr('manifest.json',
            serialize(
                'manifest',
                self.get_queryset(),
                version=kwargs['version']
            )
        )

        for canvas in manifest.canvas_set.all():
            annotation_file = "annotation_list_" + canvas.pid + ".json"
            zf.writestr(
                annotation_file,
                serialize(
                    'annotation_list',
                    [canvas],
                    version=kwargs['version']
                )
            )

#        finally:
            # Remove our temporary directory
#            shutil.rmtree(tmpdir, ignore_errors=True)

    # Must close zip for all contents to be written
        zf.close()

        # Grab ZIP file from in-memory, make response with correct MIME-type
        resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
        # ..and correct content-disposition
        resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

        return resp
