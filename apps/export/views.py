"""Django views for manifests"""
import logging
from os import environ
from slugify import slugify
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic.base import TemplateView
from apps.export.export import IiifManifestExport
from apps.export.github import GithubApi
from apps.export.tasks import github_export_task
from apps.export.tasks import download_export_task
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.models import Manifest
from .forms import JekyllExportForm

LOGGER = logging.getLogger(__name__)

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

        export_form = JekyllExportForm(self.request.user, data=request.POST)
        export_form.is_valid()
        cleaned_data = export_form.clean()

        export_mode = export_form.cleaned_data['mode']

        if 'github_repo' not in cleaned_data:
            # If the person used spaces, `github_repo` will not be in `cleaned_data`
            github_repo = slugify(request.POST['github_repo'], lowercase=False, max_length=50)
        elif 'github_repo' in cleaned_data and not cleaned_data['github_repo']:
            # if `github_repo` was left blank, it will be an empty `str`
            github_repo = slugify(manifest.label, lowercase=False, max_length=50)
        else:
            github_repo = cleaned_data['github_repo']

        owners = [request.user.id] # TODO switch to form group vs. solo control

        # TODO Actually use the git repo and export mode
        if export_mode == 'download':
            context = self.get_context_data()
            manifest_pid = manifest.pid
            if environ['DJANGO_ENV'] != 'test': # pragma: no cover
                download_export_task.delay(
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

        if environ['DJANGO_ENV'] != 'test': # pragma: no cover
            github_export_task.delay(
                manifest_pid,
                kwargs['version'],
                github_repo=github_repo,
                deep_zoom=False,
                owner_ids=owners,
                user_id=self.request.user.id
            )
        else:
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
        context['repo_link'] = f'https://github.com/{GithubApi.github_username(self.request.user)}/{github_repo}'
        context['site_link'] = f'https://{GithubApi.github_username(self.request.user)}.github.io/{github_repo}'
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
