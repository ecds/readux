from urllib.parse import urlencode
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from ..iiif.kollections.models import Collection
from ..iiif.canvases.models import Canvas
from ..iiif.manifests.models import Manifest
from ..iiif.annotations.models import Annotation
from django.views.generic.base import RedirectView
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
        context['user_annotation'] = Annotation.objects.filter(owner_id=self.request.user.id)
        context['user_annotation_count'] = Annotation.objects.filter(owner_id=self.request.user.id).count()
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
        context['user_annotation_page_count'] = Annotation.objects.filter(owner_id=self.request.user.id).filter(canvas__id=canvas.id).count()
        context['user_annotation_count'] = Annotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=manifest.id).count()
        return context

class VolumeAllDetail(TemplateView):
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
        return context

class PageDetail(TemplateView):
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        context['page'] = canvas
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
        context['user_annotation_page_count'] = Annotation.objects.filter(owner_id=self.request.user.id).filter(canvas__id=canvas.id).count()
        context['user_annotation_count'] = Annotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=manifest.id).count()
        qs = Canvas.objects.all()

        try:
          search_string = self.request.GET['q']
          if search_string:
              query = SearchQuery(search_string)
              vector = SearchVector('annotation__content')
              qs = qs.annotate(search=vector).filter(search=query).filter(manifest__label=manifest.label)
              qs = qs.annotate(rank=SearchRank(vector, query)).order_by('-rank')
              qs1 = qs.exclude(annotation__resource_type='dctypes:Text').distinct()
              qs2 = qs.filter(annotation__owner_id=self.request.user.id)
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


class ExportOptions(TemplateView):
    template_name = "export.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context
