from django.db import models
from django import forms
from wagtail.core.models import Page, Orderable
from modelcluster.models import ClusterableModel
from wagtail.core.fields import RichTextField, StreamField
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtailautocomplete.edit_handlers import AutocompletePanel
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel
from urllib.parse import urlencode
from urllib.parse import urlencode
from django.http.response import Http404
from django.http import request

from .blocks import BaseStreamBlock
from apps.readux.models import UserAnnotation
from ..iiif.kollections.models import Collection
from ..iiif.manifests.models import Manifest
from ..iiif.canvases.models import Canvas
from ..iiif import manifests
import urllib.request

class ContentPage(Page):
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

class CollectionsPage(Page):
    page_title = models.TextField(blank=True)
    tagline = models.TextField(blank=True)
    paragraph = models.TextField(blank=True)
    layout = models.CharField(max_length=20, choices = (("Grid", "Grid"),
            ("List", "List"),("Banner", "Banner")),
            default = "List",
            help_text="Select to show all volumes as a list or a grid of icons.")
    collections = Collection.objects.all
    volumes = Manifest.objects.all
    content_panels = Page.content_panels + [
        FieldPanel('page_title', classname="full"),
        FieldPanel('tagline', classname="full"),
        FieldPanel('paragraph', classname="full"),
        FieldPanel('layout', classname="full"),
    ]

class VolumesPage(Page):
    page_title = models.TextField(blank=True)
    tagline = models.TextField(blank=True)
    paragraph = models.TextField(blank=True)
    layout = models.CharField(max_length=20, choices = (("Grid", "Grid"),
            ("List", "List"),),
            default = "Grid",
            help_text="Select to show all volumes as a list or a grid of icons.")
    collections = Collection.objects.all
    volumes = Manifest.objects.all
    content_panels = Page.content_panels + [
        FieldPanel('page_title', classname="full"),
        FieldPanel('tagline', classname="full"),
        FieldPanel('paragraph', classname="full"),
        FieldPanel('layout', classname="full"),
    ]
#     def get_context(self, request):
#         context = super(VolumesPage, self).get_context(request)
#         sort_order = self.get_sort(request)
#         volumes = Manifest.objects.all().order_by(sort_order)
#         context['sort'] = request.GET.get('sort', 'created_at')
#         context['volumes'] = volumes
#         return context
#         
#     def get_sort(self, request):
#         if request.GET.get('sort', 'created_at') == 'created_at':
#             return '-created_at'
#         else:
#             return 'label'
        

    def get_context(self, request):
        context = super().get_context(request)
        sort = request.GET.get('sort', None)
        order = request.GET.get('order', None)
        
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

        sort_url_params = request.GET.copy()
        order_url_params = request.GET.copy()
        if 'sort' in sort_url_params and 'order' in order_url_params:
            del sort_url_params['sort']
            del order_url_params['order']
        elif 'sort' in sort_url_params:
            del sort_url_params['sort']
        elif 'order' in order_url_params:
            del order_url_params['order']
       
        context['volumespage'] = q.all
        context['user_annotation'] = UserAnnotation.objects.filter(owner_id=request.user.id)
        annocount_list = []
        canvaslist = []
        for volume in q:
            user_annotation_count = UserAnnotation.objects.filter(owner_id=request.user.id).filter(canvas__manifest__id=volume.id).count()
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
        'sort': sort, 'sort_options': sort_options,
        'order': order, 'order_options': order_options,
                     })
        return context


class HomePage(Page):
    tagline = models.TextField(blank=True)
    content_display = models.CharField(max_length=20, choices = (("Collections", "Collections"),
            ("Volumes", "Volumes"),),
            default = "Collections",
            help_text="Select to show all collections or all volumes on the home page")
    featured_collections = ParentalManyToManyField(Collection, null=True, blank=True)
    featured_collections_sort_order = models.CharField(max_length=20, choices = (
            ("label", "Title"),
            ("created_at", "Input Date"),),
            default = "label",
            help_text="Select order to sort collections on home page")
    featured_volumes = ParentalManyToManyField(Manifest, null=True, blank=True)
    featured_volumes_sort_order = models.CharField(max_length=20, choices = (
            ("label", "Title"),
            ("created_at", "Input Date"),
            ("author", "Author"),
            ("published_date", "Publication Date"),),
            default = "label",
            help_text="Select order to sort volumes on home page")
    collections = Collection.objects.all
    volumes = Manifest.objects.all

    content_panels = Page.content_panels + [
        FieldPanel('tagline', classname="full"),
        FieldPanel('content_display', classname="full"),
        #FieldPanel('featured_collections', widget=forms.CheckboxSelectMultiple, classname="full"),
        AutocompletePanel('featured_collections', target_model="kollections.Collection"),
        FieldPanel('featured_collections_sort_order', classname="full"),
        AutocompletePanel('featured_volumes', target_model="manifests.Manifest"),
        #FieldPanel('featured_volumes', widget=forms.CheckboxSelectMultiple, classname="full"),
        FieldPanel('featured_volumes_sort_order', classname="full"),
    ]


    def get_context(self, request):
        context = super().get_context(request)
        q = Manifest.objects.all()

        context['volumespage'] = q.all
        context['user_annotation'] = UserAnnotation.objects.filter(owner_id=request.user.id)
        annocount_list = []
        canvaslist = []
        for volume in q:
            user_annotation_count = UserAnnotation.objects.filter(owner_id=request.user.id).filter(canvas__manifest__id=volume.id).count()
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
        return context
