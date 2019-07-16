from django.db import models
from django import forms
from wagtail.core.models import Page
from modelcluster.models import ClusterableModel
from wagtail.core.fields import RichTextField, StreamField
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtailautocomplete.edit_handlers import AutocompletePanel
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel, InlinePanel

from .blocks import BaseStreamBlock
from ..iiif.kollections.models import Collection
from ..iiif.manifests.models import Manifest
from ..iiif import manifests



class ContentPage(Page):
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

# class CollectionsPage(Page):
#     page_title = models.TextField(blank=True)
#     tagline = models.TextField(blank=True)
#     page_text = models.TextField(blank=True)
#     collections = Collection.objects.all
#     volumes = Manifest.objects.all
#     content_panels = Page.content_panels + [
#         FieldPanel('tagline', classname="full"),
#     ]
# 
# class VolumesPage(Page):
#     page_title = models.TextField(blank=True)
#     tagline = models.TextField(blank=True)
#     page_text = models.TextField(blank=True)
#     collections = Collection.objects.all
#     volumes = Manifest.objects.all
#     content_panels = Page.content_panels + [
#         FieldPanel('tagline', classname="full"),
#     ]
#     def get_context(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         sort = self.request.GET.get('sort', None)
# 
#         q = Manifest.objects.all()
# 
#         sort_options = ['title', 'author', 'date published', 'date added']
#         if sort not in sort_options:
#             sort = 'title'
# 
#         if sort == 'title':
#             q = q.order_by('label')
#         elif sort == 'author':
#             q = q.order_by('author')
#         elif sort == 'date published':
#             q = q.order_by('published_date')
#         elif sort == 'date added':
#             q = q.order_by('-created_at')
# 
#         sort_url_params = self.request.GET.copy()
#         if 'sort' in sort_url_params:
#             del sort_url_params['sort']
# 
#         context['volumes'] = q.all
#         context.update({
#         'sort_url_params': urlencode(sort_url_params),
#         'sort': sort, 'sort_options': sort_options,
#                      })
#         return context


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
        FieldPanel('featured_collections', widget=forms.CheckboxSelectMultiple, classname="full"),
        FieldPanel('featured_collections_sort_order', classname="full"),
        AutocompletePanel('featured_volumes', target_model="manifests.Manifest"),
        #FieldPanel('featured_volumes', widget=forms.CheckboxSelectMultiple, classname="full"),
        FieldPanel('featured_volumes_sort_order', classname="full"),
    ]
