from urllib.parse import urlencode
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from ..iiif.kollections.models import Collection
from ..iiif.canvases.models import Canvas
from ..iiif.manifests.models import Manifest
from ..iiif.annotations.models import Annotation
from django.views.generic.base import RedirectView

class CollectionsList(ListView):
    template_name = "collections.html"

    context_object_name = 'collections'
    queryset = Collection.objects.all()

class CollectionDetail(TemplateView):
    template_name = "collection.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)

        q = Collection.objects.filter(pid=kwargs['collection']).first().manifests

        sort_options = ['title', 'author', 'date published', 'date added']
        if sort not in sort_options:
            sort = 'title'

        if sort == 'title':
            q = q.order_by('label')
        elif sort == 'author':
            q = q.order_by('author')
        elif sort == 'date published':
            q = q.order_by('published_date')
        elif sort == 'date added':
            q = q.order_by('-created_at')

        sort_url_params = self.request.GET.copy()
        if 'sort' in sort_url_params:
            del sort_url_params['sort']

        context['collection'] = Collection.objects.filter(pid=kwargs['collection']).first()
        context['volumes'] = q.all
        context.update({
        'sort_url_params': urlencode(sort_url_params),
        'sort': sort, 'sort_options': sort_options,
                     })
        return context

class VolumeDetail(TemplateView):
    template_name = "volume.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context

class PageDetail(TemplateView):
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = Canvas.objects.filter(pid=kwargs['page']).first()
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
        context['user_annotation_count'] = Annotation.objects.filter(owner_id=self.request.user.id).filter(canvas__manifest__id=manifest.id).count()
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
