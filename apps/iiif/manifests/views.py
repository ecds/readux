"""Django views for manifests"""
import csv
from io import StringIO
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

from apps.ingest.services import normalize_header, set_metadata
from .models import Manifest
from .forms import ManifestCSVImportForm, ManifestsCollectionsForm

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

class AllVolumesCollection(View):
    """Endpoint for all volumes collection."""
    def get_queryset(self):
        """Get all manifest objects.

        :return: All manifest objects
        :rtype: django.db.models.QuerySet
        """
        return Manifest.objects.all()

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """Responds to HTTP GET request for all manifests.

        :return: IIIF representation of all volumes collection
        :rtype: JSON
        """
        collection = {
            "@id": request.build_absolute_uri(),
            "@type": "sc:Collection",
            "@context": "http://iiif.io/api/presentation/2/context.json",
            "label": "All Readux volumes",
            "manifests": json.loads(
                serialize(
                    'all_volumes_manifest',
                    self.get_queryset(),
                    is_list=True
                )
            )
        }

        return JsonResponse(collection,safe=False)

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

class MetadataImportView(FormView):
    """Admin page to import a CSV and update multiple Manifests' metadata"""

    template_name = 'manifest_metadata_import.html'
    form_class = ManifestCSVImportForm

    def get_context_data(self, **kwargs):
        """Set page title on context data"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Manifest metadata bulk update (CSV import)'
        return context

    def form_valid(self, form):
        """Read the CSV file and, find associated manifests, and update metadata"""
        csv_file = form.cleaned_data.get('csv_file')
        csv_io = StringIO(csv_file.read().decode('utf-8'))
        reader = csv.DictReader(normalize_header(csv_io))
        for row in reader:
            try:
                # try to find manifest
                manifest = Manifest.objects.get(pid=row['pid'])
                # use ingest set_metadata function
                set_metadata(manifest, metadata=row)
            except Manifest.DoesNotExist:
                messages.add_message(
                    self.request, messages.ERROR, f'Manifest with pid {row["pid"]} not found'
                )
        return super().form_valid(form)

    def get_success_url(self):
        """Return to the manifest change list with a success message"""
        messages.add_message(
            self.request, messages.SUCCESS, 'Successfully updated manifests'
        )
        return reverse('admin:manifests_manifest_changelist')
