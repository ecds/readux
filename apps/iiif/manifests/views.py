"""Django views for manifests"""
import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic.base import TemplateView
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.users.models import User
from ..canvases.models import Canvas
from .models import Manifest
from .export import IiifManifestExport
from .forms import JekyllExportForm
from .tasks import github_export_task
from .tasks import download_export_task

LOGGER = logging.getLogger(__name__)

class ManifestDetail(View):
    """Endpoint for a specific IIIF manifest."""
    def get_queryset(self):
        """Get requested manifest object.

        :return: Manifest object
        :rtype: django.db.models.QuerySet
        """
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """Responds to HTTP GET request for specific manifest.

        :return: IIIF representation of a manifest/volume
        :rtype: JSON
        """
        manifest = self.get_queryset()[0].id
        annotators = User.objects.filter(annotation__canvas__manifest__id=manifest).distinct()
        annotators_string = ', '.join([str(i.name) for i in annotators])
        return JsonResponse(
            json.loads(
                serialize(
                    'manifest',
                    self.get_queryset(),
                    version=kwargs['version'],
                    annotators=annotators_string,
                    exportdate=datetime.utcnow()
                )
            ),
            safe=False)

class ManifestSitemap(Sitemap):
    """Django site map for mainfests"""
    # priority unknown
    def items(self):
        return Manifest.objects.all()

    def location(self, item):
        return reverse('ManifestRender', kwargs={'version': 'v2', 'pid': item.pid})

class ManifestRis(TemplateView):
    """Manifest Ris"""
    content_type = 'application/x-research-info-systems; charset=UTF-8'
    template_name = "citation.ris"

    def get_context_data(self, **kwargs):
        """Context data for view

        :return: [description]
        :rtype: [type]
        """
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context


class ManifestExport(View):
    """View for maifest export."""

    def get_queryset(self):
        """Get requested manifest

        :return: Manifest object to be exported.
        :rtype: django.db.models.QuerySet
        """
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def post(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """[summary]

        :param request: [description]
        :type request: [type]
        :return: [description]
        :rtype: [type]
        """
        # we should probably move this out of the view, into a library
        manifest = self.get_queryset()[0]
        owners = [request.user.id]

        zip = IiifManifestExport.get_zip(manifest, kwargs['version'], owners=owners)
        resp = HttpResponse(zip, content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=iiif_export.zip'

        return resp

class JekyllExport(TemplateView):
    """Jekyll Export view"""
    template_name = "jekyll_export.html"

    form_class = JekyllExportForm

    def get_queryset(self):
        """Get requested manifest.

        :return: Manifest to be exported.
        :rtype: apps.iiif.manifests.models.Manifest
        """
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def post(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """HTTP POST for manifest export."""
        # we should probably move this out of the view, into a library
        manifest = self.get_queryset()[0]
        LOGGER.debug(request.POST)
        LOGGER.debug(dir(self.args))

        export_form = JekyllExportForm(self.request.user, data=request.POST)

        # FIXME this needs to return an error.
        if not export_form.is_valid():
            LOGGER.debug("Export form is not valid: %s", export_form.errors)
        cleaned_data = export_form.clean()
        LOGGER.debug("Cleaned Data: %s", dir(cleaned_data))

        export_mode = export_form.cleaned_data['mode']
        github_repo = export_form.cleaned_data['github_repo']

        owners = [request.user.id] # TODO switch to form group vs. solo control

        # TODO Actually use the git repo and export mode
        if export_mode == 'download':
            context = self.get_context_data()
            manifest_pid = manifest.pid
            download_export_task(
                manifest_pid,
                kwargs['version'],
                github_repo=github_repo,
                deep_zoom=False,
                owner_ids=owners,
                user_id=self.request.user.id
            )
            context['email'] = request.user.email
            context['mode'] = "download"
            return render(request, self.template_name, context)

        #github exports
        context = self.get_context_data()
        manifest_pid = manifest.pid
        github_export_task(
            manifest_pid,
            kwargs['version'],
            github_repo=github_repo,
            deep_zoom=False,
            owner_ids=owners,
            user_id=self.request.user.id
        )

        context['email'] = request.user.email
        context['mode'] = "github"
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context_data = super(JekyllExport, self).get_context_data(**kwargs)
        return context_data

class PlainExport(View):
    """Plain export"""
    def get_queryset(self):
        """Get requested manifest

        :return: Manifest to be exported.
        :rtype: apps.iiif.manifests.models.Manifest
        """
        manifest = Manifest.objects.get(pid=self.kwargs['pid'])
        return Canvas.objects.filter(manifest=manifest.id).order_by('position')

    def get(self, request, *args, **kwargs):
        """HTTP GET endpoint for plain export.

        :rtype: django.http.HttpResponse
        """
        annotations = []
        for canvas in self.get_queryset() :
            annotations.append(canvas.result)
        return HttpResponse(' '.join(annotations))
