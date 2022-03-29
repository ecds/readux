"""Django Views for the Readux app"""
from os import path
from urllib.parse import urlencode
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormMixin
from django.contrib.sitemaps import Sitemap
from django.db.models import Max, Q, Count
from django.urls import reverse
from elasticsearch_dsl.query import MultiMatch
from apps.iiif.manifests.documents import ManifestDocument
from apps.readux.forms import ManifestSearchForm
import config.settings.local as settings
from apps.export.export import JekyllSiteExport
from apps.export.forms import JekyllExportForm
from .models import UserAnnotation
from ..cms.models import Page, CollectionsPage, VolumesPage
from ..iiif.kollections.models import Collection
from ..iiif.canvases.models import Canvas
from ..iiif.manifests.models import Manifest

SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
ORDER_OPTIONS = ['asc', 'desc']

class CollectionsList(ListView):
    """Django List View for :class:`apps.iiif.kollections.models.Collection`s"""
    template_name = "collections.html"

    context_object_name = 'collections'
    queryset = Collection.objects.all()

class VolumesList(ListView):
    """Django List View for :class:`apps.iiif.manifests.models.Manifest`s"""
    template_name = "volumes.html"
    SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
    ORDER_OPTIONS = ['asc', 'desc']
    context_object_name = 'volumes'

    def get_queryset(self):
        return Manifest.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)

        q = self.get_queryset()

        if sort not in SORT_OPTIONS:
            sort = 'title'
        if order not in ORDER_OPTIONS:
            order = 'asc'

        if sort == 'title':
            if order == 'asc':
                q = q.order_by('label')
            elif order == 'desc':
                q = q.order_by('-label')
        elif sort == 'author':
            if order == 'asc':
                q = q.order_by('author')
            elif order == 'desc':
                q = q.order_by('-author')
        elif sort == 'date published':
            if order == 'asc':
                q = q.order_by('published_date')
            elif order == 'desc':
                q = q.order_by('-published_date')
        elif sort == 'date added':
            if order == 'asc':
                q = q.order_by('created_at')
            elif order == 'desc':
                q = q.order_by('-created_at')

        sort_url_params = {'sort': sort, 'order': order}
        order_url_params = {'sort': sort, 'order': order}
        if 'sort' in sort_url_params:
            del sort_url_params['sort']

        context['volumes'] = q.all
        context.update({
            'sort_url_params': urlencode(sort_url_params),
            'order_url_params': urlencode(order_url_params),
            'sort': sort, 'SORT_OPTIONS': SORT_OPTIONS,
            'order': order, 'ORDER_OPTIONS': ORDER_OPTIONS,
        })
        return context

class CollectionDetail(ListView):
    """Django Template View for a :class:`apps.iiif.kollections.models.Collection`"""
    template_name = "collection.html"
    SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
    ORDER_OPTIONS = ['asc', 'desc']
    paginate_by = 10

    def get_queryset(self):
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)
        q = Collection.objects.filter(pid=self.kwargs['collection']).first().manifests.all()

        if sort is None:
            sort = 'title'
        if order is None:
            order = 'asc'

        if sort == 'title':
            if order == 'asc':
                q = q.order_by('label')
            elif order == 'desc':
                q = q.order_by('-label')
        elif sort == 'author':
            if order == 'asc':
                q = q.order_by('author')
            elif order == 'desc':
                q = q.order_by('-author')
        elif sort == 'date published':
            if order == 'asc':
                q = q.order_by('published_date')
            elif order == 'desc':
                q = q.order_by('-published_date')
        elif sort == 'date added':
            if order == 'asc':
                q = q.order_by('created_at')
            elif order == 'desc':
                q = q.order_by('-created_at')

        return 	q

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)

        q = Collection.objects.filter(pid=self.kwargs['collection']).first().manifests

        if sort is None:
            sort = 'title'
        if order is None:
            order = 'asc'

        if sort == 'title':
            if order == 'asc':
                q = q.order_by('label')
            elif order == 'desc':
                q = q.order_by('-label')
        elif sort == 'author':
            if order == 'asc':
                q = q.order_by('author')
            elif order == 'desc':
                q = q.order_by('-author')
        elif sort == 'date published':
            if order == 'asc':
                q = q.order_by('published_date')
            elif order == 'desc':
                q = q.order_by('-published_date')
        elif sort == 'date added':
            if order == 'asc':
                q = q.order_by('created_at')
            elif order == 'desc':
                q = q.order_by('-created_at')

        sort_url_params = self.request.GET.copy()
        order_url_params = self.request.GET.copy()
#         if 'sort' in sort_url_params:
#             del sort_url_params['sort']

        context['collectionlink'] = Page.objects.type(CollectionsPage).first()
        context['collection'] = Collection.objects.filter(pid=self.kwargs['collection']).first()
        context['volumes'] = q.all
        context['manifest_query_set'] = q
        context['user_annotation'] = UserAnnotation.objects.filter(owner_id=self.request.user.id)
        value = 0
        context['value'] = value
        context.update({
            'sort_url_params': urlencode(sort_url_params),
            'order_url_params': urlencode(order_url_params),
            'sort': sort, 'SORT_OPTIONS': SORT_OPTIONS,
            'order': order, 'ORDER_OPTIONS': ORDER_OPTIONS,
        })
        return context

class VolumeDetail(TemplateView):
    """Django Template View for :class:`apps.iiif.manifest.models.Manifest`"""
    template_name = "volume.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context

# FIXME: What is this used for? The template does not exist.
class AnnotationsCount(TemplateView):
    """Django Template View for :class:`apps.readux.models.UserAnnotation`"""
    template_name = "count.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        context['page'] = canvas
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
        context['user_annotation_page_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__id=canvas.id
        ).count()
        context['user_annotation_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__manifest__id=manifest.id
        ).count()
        return context

class PageDetail(TemplateView):
    """Django Template View for :class:`apps.iiif.canvases.models.Canvas`"""
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manifest = Manifest.objects.get(pid=kwargs['volume'])
        if 'page' in kwargs:
            canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        else:
            canvas = manifest.canvas_set.all().first()
        # if 'page' in kwargs and kwargs['page'] == 'all':
        #     context['all'] = True
        context['page'] = canvas
        context['volume'] = manifest
        context['pagelink'] = manifest.image_server
        context['collectionlink'] = Page.objects.type(CollectionsPage).first()
        context['volumelink'] = Page.objects.type(VolumesPage).first()
        context['user_annotation_page_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__id=canvas.id
        ).count()
        context['user_annotation_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__manifest__id=manifest.id
        ).count()
        context['mirador_url'] = settings.MIRADOR_URL

        user_annotation_index = UserAnnotation.objects.all()

        user_annotation_index = user_annotation_index.filter(canvas__manifest__label=manifest.label)

        user_annotation_index = user_annotation_index.filter(owner_id=self.request.user.id).distinct()

        user_annotation_index = user_annotation_index.values(
                 'canvas__position',
                 'canvas__manifest__label',
                 'canvas__pid'
             ).annotate(
                 Count(
                     'canvas__position')
                 ).order_by('canvas__position')

        context['user_annotation_index'] = user_annotation_index
        context['json_data'] = {'json_data': list(user_annotation_index)}

        return context

class ExportOptions(TemplateView, FormMixin):
    """Django Template View for Export"""
    template_name = "export.html"
    form_class = JekyllExportForm

    def get_form_kwargs(self):
        # keyword arguments needed to initialize the form
        kwargs = super(ExportOptions, self).get_form_kwargs()
        # add user, which is used to determine available groups
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['export_form'] = self.get_form()
        return context

class ExportDownload(TemplateView):
    """Django Template View for downloading an export."""
    template_name = "export_download.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        filename = kwargs['filename']
        context['filename'] = filename
        # check to see if the file exists
        if path.exists(JekyllSiteExport.get_zip_path(filename)):
            context['file_exists'] = True
        else:
            context['file_exists'] = False

        return context

class ExportDownloadZip(View):
    """Django View for downloading the zipped up export."""
    def get(self, request, *args, **kwargs):
        """[summary]

        :param View: [description]
        :type View: [type]
        :param request: [description]
        :type request: [type]
        :return: [description]
        :rtype: [type]
        """
        jekyll_export = JekyllSiteExport(None, "v2", github_repo=None, deep_zoom=False, owners=[self.request.user.id], user=self.request.user);
        zip = jekyll_export.get_zip_file(kwargs['filename'])
        resp = HttpResponse(zip, content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=jekyll_site_export.zip'
        return resp

class VolumeSearchView(ListView, FormMixin):
    """View to search across all volumes with Elasticsearch"""
    model = Manifest
    form_class = ManifestSearchForm
    template_name = "search_results.html"
    context_object_name = "volumes"
    paginate_by = 25
    # default fields to search when using query box; ^ with number indicates a boosted field
    query_search_fields = ["pid", "label^3", "summary", "authors"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # use GET for form data so that query params appear in URL
        form_data = self.request.GET.copy()
        kwargs["data"] = form_data
        return kwargs

    def get_queryset(self):
        form = self.get_form()
        if not form.is_valid():
            return Manifest.objects.none()

        volumes = ManifestDocument.search()

        form_data = form.cleaned_data
        # default to empty string if no query in form data
        search_query = form_data.get("q", "")
        if search_query:
            multimatch_query = MultiMatch(query=search_query, fields=self.query_search_fields)
            volumes = volumes.query(multimatch_query)

        # return elasticsearch_dsl Search instance
        return volumes


# TODO: Replace with Elasticsearch
# class VolumeSearch(ListView):
#     '''Search across all volumes.'''
#     template_name = 'search_results.html'

#     def get_queryset(self):
#         return Manifest.objects.all()

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         collection = self.request.GET.get('collection', None)
#         # pylint: disable = invalid-name
#         COLSET = Collection.objects.values_list('pid', flat=True)
#         COL_OPTIONS = list(COLSET)
#         COL_LIST = Collection.objects.values('pid', 'label').order_by('label').distinct('label')
#         # pylint: enable = invalid-name
#         collection_url_params = self.request.GET.copy()

#         qs = self.get_queryset()
#         try:
#             search_string = self.request.GET['q']
#             search_type = self.request.GET['type']
#             search_strings = self.request.GET['q'].split()
#             if search_strings:
#                 if search_type == 'partial':
#                     qq = Q()
#                     qqq = Q()
#                     query = SearchQuery('')
#                     for search_string in search_strings:
#                         query = query | SearchQuery(search_string)
#                         qq |= Q(canvas__annotation__content__icontains=search_string)
#                         qqq |= Q(label__icontains=search_string) |Q(author__icontains=search_string) | Q(summary__icontains=search_string) # pylint: disable = line-too-long
#                     qs1 = qs.filter(qq)
#                     qs1 = qs1.values(
#                         'pid', 'label', 'author',
#                         'published_date', 'created_at'
#                     ).annotate(
#                         pidcount=Count('pid')
#                     ).order_by('-pidcount')

#                     vector2 = SearchVector(
#                         'label', weight='A'
#                     ) + SearchVector(
#                         'author', weight='B'
#                     ) + SearchVector(
#                         'summary', weight='C'
#                     )

#                     qs3 = qs.filter(qqq)
#                     qs2 = qs.values(
#                         'label', 'author', 'published_date', 'created_at', 'canvas__pid', 'pid',
#                         'canvas__manifest__image_server__server_base'
#                     ).order_by(
#                         'pid'
#                     ).distinct(
#                         'pid'
#                     )

#                     if collection not in COL_OPTIONS:
#                         collection = None

#                     if collection is not None:
#                         qs1 = qs1.filter(collections__pid = collection)
#                         qs3 = qs3.filter(collections__pid = collection)

#                     if 'collection' in collection_url_params:
#                         del collection_url_params['collection']
#                 elif search_type == 'exact':
#                     qq = Q()
#                     query = SearchQuery('')
#                     for search_string in search_strings:
#                         query = query | SearchQuery(search_string)
#                         qq |= Q(canvas__annotation__content__exact=search_string)
#                     vector = SearchVector('canvas__annotation__content')
#                     qs1 = qs.annotate(search=vector).filter(search=query)
#                     qs1 = qs1.annotate(
#                         rank=SearchRank(vector, query)
#                     ).values(
#                         'pid', 'label', 'author',
#                         'published_date', 'created_at'
#                     ).annotate(
#                         pidcount = Count('pid')
#                     ).order_by('-pidcount')

#                     vector2 = SearchVector(
#                         'label', weight='A'
#                     ) + SearchVector(
#                         'author', weight='B'
#                     ) + SearchVector(
#                         'summary', weight='C'
#                     )

#                     qs3 = qs.annotate(search=vector2).filter(search=query)
#                     qs3 = qs3.annotate(
#                         rank=SearchRank(vector2, query)
#                     ).values(
#                         'pid', 'label', 'author',
#                         'published_date', 'created_at'
#                     ).order_by('-rank')

#                     qs2 = qs.values(
#                         'canvas__pid', 'pid',
#                         'canvas__manifest__image_server__server_base'
#                     ).order_by(
#                         'pid'
#                     ).distinct('pid')

#                     if collection not in COL_OPTIONS:
#                         collection = None

#                     if collection is not None:
#                         qs1 = qs1.filter(collections__pid = collection)
#                         qs3 = qs3.filter(collections__pid = collection)

#                     if 'collection' in collection_url_params:
#                         del collection_url_params['collection']
#             else:
#                 search_string = ''
#                 search_strings = ''
#                 qs1 = ''
#                 qs2 = ''
#                 qs3 = ''
#             context['qs1'] = qs1
#             context['qs2'] = qs2
#             context['qs3'] = qs3
#         except MultiValueDictKeyError:
#             q = ''
#             search_string = ''
#             search_strings = ''

#         context['volumes'] = qs.all
#         annocount_list = []
#         canvaslist = []
#         for volume in qs:
#             user_annotation_count = UserAnnotation.objects.filter(
#                 owner_id=self.request.user.id
#             ).filter(
#                 canvas__manifest__id=volume.id
#             ).count()
#             annocount_list.append({volume.pid: user_annotation_count})
#             context['user_annotation_count'] = annocount_list
#             canvasquery = Canvas.objects.filter(is_starting_page=1).filter(manifest__id=volume.id)
#             canvasquery2 = list(canvasquery)
#             canvaslist.append({volume.pid: canvasquery2})
#             context['firstthumbnail'] = canvaslist
#         context.update({
#             'collection_url_params': urlencode(collection_url_params),
#             'collection': collection, 'COL_OPTIONS': COL_OPTIONS,
#             'COL_LIST': COL_LIST, 'search_string': search_string, 'search_strings': search_strings
#         })
#         return context

class ManifestsSitemap(Sitemap):
    """Django Sitemap for Manafests"""
    limit = 5
    # priority unknown
    def items(self):
        return Manifest.objects.all()

    def location(self, item):
        return reverse('volumeall', kwargs={'volume': item.pid})

    def lastmod(self, item):
        return item.updated_at

class CollectionsSitemap(Sitemap):
    """Django Sitemap for Collections"""
    # priority unknown
    def items(self):
        return Collection.objects.all().annotate(modified_at=Max('manifests__updated_at'))

    def location(self, item):
        return reverse('collection', kwargs={'collection': item.pid})

    def lastmod(self, item):
        return item.updated_at
