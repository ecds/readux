from django.db import models
from ..iiif.kollections.models import Collection
from ..iiif.manifests.models import Manifest

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel

from .blocks import BaseStreamBlock


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
    featured_collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True)
    featured_volume = models.ForeignKey(Manifest, on_delete=models.SET_NULL, null=True, blank=True)
    collections = Collection.objects.all
    volumes = Manifest.objects.all

    content_panels = Page.content_panels + [
        FieldPanel('tagline', classname="full"),
        FieldPanel('content_display', classname="full"),
        FieldPanel('featured_collection', classname="full"),
        FieldPanel('featured_volume', classname="full"),
    ]
