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
from django.views.generic.base import RedirectView
from django.views.generic.edit import FormMixin
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Q

class CollectionsList(ListView):
    template_name = "collections.html"

    context_object_name = 'collections'
    queryset = Collection.objects.all()

class VolumesList(ListView):
    template_name = "volumes.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)

        q = Manifest.objects.all()

        sort_options = ['title', 'author', 'date published', 'date added']
        order_options = ['asc', 'desc']
        if sort not in sort_options and order not in order_options:
            sort = 'title'
            order = 'asc'
        elif sort not in sort_options:
            sort = 'title'
        elif order not in order_options:
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

        context['volumes'] = q.all
        context.update({
        'sort_url_params': urlencode(sort_url_params),
        'order_url_params': urlencode(order_url_params),
        'sort': sort, 'sort_options': sort_options,
        'order': order, 'order_options': order_options,
                     })
        return context
    context_object_name = 'volumes'
    queryset = Manifest.objects.all()

class CollectionDetail(TemplateView):
    template_name = "collection.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)

        q = Collection.objects.filter(pid=kwargs['collection']).first().manifests

        sort_options = ['title', 'author', 'date published', 'date added']
        order_options = ['asc', 'desc']
        if sort not in sort_options and order not in order_options:
            sort = 'title'
            order = 'asc'
        elif sort not in sort_options:
            sort = 'title'
        elif order not in order_options:
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

        context['collection'] = Collection.objects.filter(pid=kwargs['collection']).first()
        context['volumes'] = q.all
        context['user_annotation'] = UserAnnotation.objects.filter(owner_id=self.request.user.id)
        context['user_annotation_count'] = UserAnnotation.objects.filter(owner_id=self.request.user.id).count()
        value = 0
        context['value'] = value
        context.update({
        'sort_url_params': urlencode(sort_url_params),
        'order_url_params': urlencode(order_url_params),
        'sort': sort, 'sort_options': sort_options,
        'order': order, 'order_options': order_options,
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

class VolumeAllDetail(TemplateView):
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        canvas = Canvas.objects.filter(position='1').first()
        context['page'] = canvas
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
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
              qs = qs.annotate(rank=SearchRank(vector, query)).order_by('-rank')
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

class PageDetail(TemplateView):
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        context['page'] = canvas
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
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
              qs = qs.annotate(rank=SearchRank(vector, query)).order_by('-rank')
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
