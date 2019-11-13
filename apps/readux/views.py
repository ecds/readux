from urllib.parse import urlencode
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from ..iiif.kollections.models import Collection
from ..iiif.canvases.models import Canvas
from ..iiif.manifests.models import Manifest
from ..iiif.annotations.models import Annotation
from ..iiif.manifests.forms import JekyllExportForm
from apps.readux.models import UserAnnotation
from apps.cms.models import Page, CollectionsPage
from django.views.generic.base import RedirectView
from django.views.generic.edit import FormMixin
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Q, Count

SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
ORDER_OPTIONS = ['asc', 'desc']

class CollectionsList(ListView):
    template_name = "collections.html"

    context_object_name = 'collections'
    queryset = Collection.objects.all()

class VolumesList(ListView):
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

        # SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
        # ORDER_OPTIONS = ['asc', 'desc']
        if sort not in SORT_OPTIONS:
            sort = 'title'
        if order not in ORDER_OPTIONS:
            order = 'asc'

        if sort == 'title':
            if(order == 'asc'):
                q = q.order_by('label')
            elif(order == 'desc'):
                q = q.order_by('-label')            
        elif sort == 'author':
            if(order == 'asc'):
                q = q.order_by('author')
            elif(order == 'desc'):
                q = q.order_by('-author')            
        elif sort == 'date published':
            if(order == 'asc'):
                q = q.order_by('published_date')
            elif(order == 'desc'):
                q = q.order_by('-published_date')            
        elif sort == 'date added':
            if(order == 'asc'):
                q = q.order_by('created_at')
            elif(order == 'desc'):
                q = q.order_by('-created_at')            

        # sort_url_params = self.request.GET.copy()
        # order_url_params = self.request.GET.copy()
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

class CollectionDetail(TemplateView):
    template_name = "collection.html"
    SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
    ORDER_OPTIONS = ['asc', 'desc']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)

        q = Collection.objects.filter(pid=self.kwargs['collection']).first().manifests

        if sort not in SORT_OPTIONS:
            sort = 'title'
        if order not in ORDER_OPTIONS:
            order = 'asc'

        if sort == 'title':
            if(order == 'asc'):
                q = q.order_by('label')
            elif(order == 'desc'):
                q = q.order_by('-label')            
        elif sort == 'author':
            if(order == 'asc'):
                q = q.order_by('author')
            elif(order == 'desc'):
                q = q.order_by('-author')            
        elif sort == 'date published':
            if(order == 'asc'):
                q = q.order_by('published_date')
            elif(order == 'desc'):
                q = q.order_by('-published_date')            
        elif sort == 'date added':
            if(order == 'asc'):
                q = q.order_by('created_at')
            elif(order == 'desc'):
                q = q.order_by('-created_at')            

        sort_url_params = self.request.GET.copy()
        order_url_params = self.request.GET.copy()
        if 'sort' in sort_url_params:
            del sort_url_params['sort']

        context['collectionlink'] = Page.objects.type(CollectionsPage).first()
        context['collection'] = Collection.objects.filter(pid=kwargs['collection']).first()
        context['volumes'] = q.all
        context['manifest_query_set'] = q
        context['user_annotation'] = UserAnnotation.objects.filter(owner_id=self.request.user.id)
        annocount_list = []
        canvaslist = []
        for volume in q:
            user_annotation_count = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=volume.id).count()
            annocount_list.append({volume.pid: user_annotation_count})
            context['user_annotation_count'] = annocount_list
            print(volume.pid)
            print(user_annotation_count)
            canvasquery = Canvas.objects.filter(is_starting_page=1).filter(manifest__id=volume.id)
            canvasquery2 = list(canvasquery)
            canvaslist.append({volume.pid: canvasquery2})
            context['firstthumbnail'] = canvaslist
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
    template_name = "volume.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context

class AnnotationsCount(TemplateView):
    template_name = "count.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        context['page'] = canvas
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
        context['user_annotation_page_count'] = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__id=canvas.id).count()
        context['user_annotation_count'] = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=manifest.id).count()
        return context

# class VolumeAllDetailOld(TemplateView):
#     template_name = "page.html"
# 
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
#         context['volume'] = manifest
#         qs = Annotation.objects.all()
# 
#         try:
#           search_string = self.request.GET['q']
#           if search_string:
#               query = SearchQuery(search_string)
#               vector = SearchVector('content')
#               qs = qs.annotate(search=vector).filter(search=query).filter(canvas__manifest__label=manifest.label)
#               qs = qs.annotate(rank=SearchRank(vector, query)).order_by('-rank')
#               qs1 = qs.exclude(resource_type='dctypes:Text').distinct()
#               qs2 = qs.filter(owner_id=self.request.user.id).distinct()
#           context['qs1'] = qs1
#           context['qs2'] = qs2
#         except MultiValueDictKeyError:
#           q = ''
#         
#         return context

# TODO Is this view still needed?
# class VolumeAllDetail(TemplateView):
#     template_name = "page.html"
# 
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         canvas = Canvas.objects.filter(position='1').first()
#         context['page'] = canvas
#         manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
#         context['volume'] = manifest
#         context['user_annotation_page_count'] = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__id=canvas.id).count()
#         context['user_annotation_count'] = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=manifest.id).count()
#         qs = Annotation.objects.all()
# 
#         try:
#           search_string = self.request.GET['q']
#           if search_string:
#               query = SearchQuery(search_string)
#               vector = SearchVector('content')
#               qs = qs.annotate(search=vector).filter(search=query).filter(canvas__manifest__label=manifest.label)
#               qs = qs.annotate(rank=SearchRank(vector, query)).order_by('-rank')
#               qs1 = qs.exclude(resource_type='dctypes:Text').distinct()
#               qs2 = qs.annotate(search=vector).filter(search=query).filter(canvas__manifest__label=manifest.label)
#               qs2 = qs2.annotate(rank=SearchRank(vector, query)).order_by('-rank')
#               qs2 = qs2.filter(owner_id=self.request.user.id).distinct()
#           else:
#               qs1 = ''
#               qs2 = ''
#           context['qs1'] = qs1
#           context['qs2'] = qs2
#         except MultiValueDictKeyError:
#           q = ''
#         
#         return context

# TODO is this still needed? Yes.
class PageDetail(TemplateView):
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'page' in kwargs:
            canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        else:
            canvas = Canvas.objects.filter(position='1').first()
        context['page'] = canvas
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
        context['collectionlink'] = Page.objects.type(CollectionsPage).first()
        context['user_annotation_page_count'] = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__id=canvas.id).count()
        context['user_annotation_count'] = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=manifest.id).count()
        qs = Annotation.objects.all()
        qs2 = UserAnnotation.objects.all()

        try:
          search_string = self.request.GET['q']
          if search_string:
              query = SearchQuery(search_string)
              vector = SearchVector('content')
              qs = qs.annotate(search=vector).filter(search=query).filter(canvas__manifest__label=manifest.label)
#              qs = qs.annotate(rank=SearchRank(vector, query)).order_by('-rank')
              qs = qs.annotate(rank=SearchRank(vector, query)).values('canvas__position', 'canvas__manifest__label', 'canvas__pid').annotate(Count('canvas__position')).order_by('canvas__position')
              qs1 = qs.exclude(resource_type='dctypes:Text').distinct()
              qs2 = qs2.annotate(search=vector).filter(search=query).filter(canvas__manifest__label=manifest.label)
              qs2 = qs2.annotate(rank=SearchRank(vector, query)).order_by('-rank')
              qs2 = qs2.filter(owner_id=self.request.user.id).distinct()
          else:
              qs1 = ''
              qs2 = ''
          context['qs1'] = qs1
          context['qs2'] = qs2
        except MultiValueDictKeyError:
          q = ''
        
        return context

# class PageRedirect(TemplateView):
#     template_name = "page.html"
# 
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['page'] = Canvas.objects.first()
#         manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
#         context['volume'] = manifest
#         context['user_annotation_count'] = Annotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=manifest.id).count()
#         return context
# class PageRedirectView(RedirectView):
# 
#     permanent = False
#     query_string = True
#     pattern_name = 'page-redirect'
# 
#     def get_redirect_url(self, *args, **kwargs):
#         page = Manifest.canvas_set.first()
#         return super().get_redirect_url(*args, **kwargs)

# TODO is this needed?
class ExportOptions(TemplateView, FormMixin):
    template_name = "export.html"
    form_class = JekyllExportForm

    def get_form_kwargs(self):
        # keyword arguments needed to initialize the form
        kwargs = super(ExportOptions, self).get_form_kwargs()
        # add user, which is used to determine available groups
        kwargs['user'] = self.request.user
        # add flag to indicate if user has a github account
#        kwargs['user_has_github'] = self.user_has_github
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['export_form'] = self.get_form()
        return context
        
class VolumeSearch(ListView):
    '''Search across all volumes.'''
    template_name = 'search_results.html'

    def get_queryset(self):
        return Manifest.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.request.GET.get('collection', None)
        COLSET = self.get_queryset().values_list('collections__pid', flat=True)
        COL_OPTIONS = list(COLSET)
        COL_LIST = self.get_queryset().values('collections__pid', 'collections__label').order_by('collections__label').distinct('collections__label')
        collection_url_params = self.request.GET.copy()
        
        qs = self.get_queryset()
        try:
          search_string = self.request.GET['q']
          if search_string:
              query = SearchQuery(search_string)
              vector = SearchVector('canvas__annotation__content')
              qs1 = qs.annotate(search=vector).filter(search=query)
              qs1 = qs1.annotate(rank=SearchRank(vector, query)).order_by('-rank')
              qs1 = qs1.annotate(rank=SearchRank(vector, query)).values('pid', 'label', 'author', 'published_date', 'created_at').annotate(pidcount = Count('pid')).order_by('-pidcount')
              qs2 = qs.values('canvas__pid', 'pid', 'canvas__IIIF_IMAGE_SERVER_BASE__IIIF_IMAGE_SERVER_BASE').order_by('pid').distinct('pid')
              if collection not in COL_OPTIONS:
                  collection = None
        
              if collection is not None:
                  print(collection)
                  qs1 = qs1.filter(collections__pid = collection)

              if 'collection' in collection_url_params:
                  del collection_url_params['collection']
#               qs1 = qs.exclude(resource_type='dctypes:Text').distinct()
#               qs2 = qs2.annotate(search=vector).filter(search=query).filter(canvas__manifest__label=manifest.label)
#               qs2 = qs2.annotate(rank=SearchRank(vector, query)).order_by('-rank')
#               qs2 = qs2.filter(owner_id=self.request.user.id).distinct()
          else:
              search_string = ''
              qs1 = ''
              qs2 = ''
          context['qs1'] = qs1
          context['qs2'] = qs2
#               qs1 = ''
#               qs2 = ''
#           context['qs1'] = qs1
#           context['qs2'] = qs2
        except MultiValueDictKeyError:
          q = ''
          search_string = ''

        context['volumes'] = qs.all
#         context['user_annotation'] = UserAnnotation.objects.filter(owner_id=self.request.user.id)
#         annocount_list = []
#         canvaslist = []
#         for volume in qs:
#             user_annotation_count = UserAnnotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=volume.id).count()
#             annocount_list.append({volume.pid: user_annotation_count})
#             context['user_annotation_count'] = annocount_list
#             print(volume.pid)
#             print(user_annotation_count)
#             canvasquery = Canvas.objects.filter(is_starting_page=1).filter(manifest__id=volume.id)
#             canvasquery2 = list(canvasquery)
#             canvaslist.append({volume.pid: canvasquery2})
#             context['firstthumbnail'] = canvaslist
#         value = 0
#         context['value'] = value
        context.update({
            'collection_url_params': urlencode(collection_url_params),
            'collection': collection, 'COL_OPTIONS': COL_OPTIONS,
            'COL_LIST': COL_LIST, 'search_string': search_string
        })
        return context
