"""Django views for manifests"""
import json
import logging
from datetime import datetime
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Manifest
from .forms import ManifestsCollectionsForm

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
        # manifest = self.get_queryset()[0].id
        # annotators = User.objects.filter(annotation__canvas__manifest__id=manifest).distinct()
        annotators = []
        if request.user.is_authenticated:
            annotators.append(request.user)
        annotators_string = ', '.join([str(i.name) for i in annotators])
        if '2' in kwargs['version']:
            return JsonResponse(
                json.loads(
                    serialize(
                        'manifest',
                        self.get_queryset(),
                        version=kwargs['version'],
                        annotators=annotators_string,
                        exportdate=datetime.utcnow(),
                        current_user=request.user
                    )
                ),
                safe=False
            )
        elif '3' in kwargs['version']:
            return JsonResponse(
                json.loads(
                    serialize(
                        'manifest_v3',
                        self.get_queryset(),
                        current_user=request.user
                    )
                ),
                safe=False
            )

class ManifestSitemap(Sitemap):
    """Django site map for manifests"""
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

class AddToCollectionsView(FormView):
    """Intermediate page to choose collections to which you are adding manifests"""

    template_name = 'add_manifests_to_collections.html'
    form_class = ManifestsCollectionsForm

    def get_context_data(self, **kwargs):
        ids = self.request.GET.get('ids', '').split(',')
        manifests = Manifest.objects.filter(pk__in=ids)
        model_admin = self.kwargs['model_admin']
        context = super().get_context_data(**kwargs)
        context['model_admin'] = model_admin.admin_site.each_context(self.request)
        context['manifests'] = manifests
        context['title'] = 'Add selected manifests to collection(s)'
        return context

    def form_valid(self, form):
        self.add_manifests_to_collections(form)
        return super().form_valid(form)

    def add_manifests_to_collections(self, form):
        """Adds selected manifests to selected collections from form"""
        context = self.get_context_data()
        manifests = context['manifests']
        if form.is_valid():
            collections = form.cleaned_data['collections']
        for manifest in manifests:
            manifest.collections.add(*collections)
            manifest.save()

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, 'Successfully added manifests to collections'
        )
        return reverse('admin:manifests_manifest_changelist')
