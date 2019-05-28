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



class ContentPage(Page):
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
    ]

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
        AutocompletePanel('featured_volumes', target_model='manifests.Manifest', is_single=False),
        #FieldPanel('featured_volumes', widget=forms.CheckboxSelectMultiple, classname="full"),
        FieldPanel('featured_volumes_sort_order', classname="full"),
    ]
