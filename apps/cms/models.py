"""CMS Models."""
from urllib.parse import urlencode
from modelcluster.fields import ParentalManyToManyField
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel
from wagtailautocomplete.edit_handlers import AutocompletePanel
from django.db import models
from apps.cms.blocks import BaseStreamBlock
from apps.readux.models import UserAnnotation
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.models import Manifest
from apps.iiif.canvases.models import Canvas
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


class ContentPage(Page):
    """Content page"""
    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True, use_json_field=False
    )

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

class CollectionsPage(Page):
    """Collections page"""
    page_title = models.TextField(blank=True)
    tagline = models.TextField(blank=True)
    paragraph = models.TextField(blank=True)
    layout = models.CharField(
        max_length=20,
        choices =(
            ("Grid", "Grid"),
            ("List", "List"),
            ("Banner", "Banner")
        ),
        default="List",
        help_text="Select to show all volumes as a list or a grid of icons."
    )
    collections = Collection.objects.all
    volumes = Manifest.objects.all
    content_panels = Page.content_panels + [
        FieldPanel('page_title', classname="full"),
        FieldPanel('tagline', classname="full"),
        FieldPanel('paragraph', classname="full"),
        FieldPanel('layout', classname="full"),
    ]


class HomePage(Page):
    """Home page"""
    tagline = RichTextField(blank=True)
    content_display = models.CharField(
        max_length=20,
        choices=(
            ("Collections", "Collections"),
            ("Volumes", "Volumes"),
        ),
        default="Collections",
        help_text="Select to show all collections or all volumes on the home page"
    )
    featured_collections = ParentalManyToManyField(Collection, blank=True)
    featured_collections_sort_order = models.CharField(
        max_length=20,
        choices=(
            ("label", "Title"),
            ("created_at", "Input Date"),
        ),
        default="label",
        help_text="Select order to sort collections on home page"
    )
    featured_volumes = ParentalManyToManyField(Manifest, blank=True)
    featured_volumes_sort_order = models.CharField(
        max_length=20,
        choices=(
            ("label", "Title"),
            ("created_at", "Input Date"),
            ("author", "Author"),
            ("published_date", "Publication Date"),
        ),
        default="label",
        help_text="Select order to sort volumes on home page"
    )
    collections = Collection.objects.all()[:8]
    volumes = Manifest.objects.all()[:8]

    content_panels = Page.content_panels + [
        FieldPanel('tagline', classname="full"),
        FieldPanel('content_display', classname="full"),
        AutocompletePanel('featured_collections', target_model="kollections.Collection"),
        FieldPanel('featured_collections_sort_order', classname="full"),
        AutocompletePanel('featured_volumes', target_model="manifests.Manifest"),
        FieldPanel('featured_volumes_sort_order', classname="full"),
    ]

    def featured_volume_count(self):
        return self.featured_volumes.all().count()

    def has_featured_volume(self):
        return self.featured_volume_count() > 0

    def get_context(self, request):
        """Function that returns context"""
        context = super().get_context(request)
        query_set = self.volumes

        # context['volumespage'] = query_set.all
        # context['user_annotation'] = UserAnnotation.objects.filter(owner_id=request.user.id)
        context['collectionsurl'] = Page.objects.type(CollectionsPage).first()
        # annocount_list = []
        # canvaslist = []
        # for volume in query_set:
        #     user_annotation_count = UserAnnotation.objects.filter(
        #         owner_id=request.user.id
        #     ).filter(
        #         canvas__manifest__id=volume.id
        #     ).count()
        #     annocount_list.append({volume.pid: user_annotation_count})
        #     context['user_annotation_count'] = annocount_list
        #     canvasquery = Canvas.objects.filter(is_starting_page=1).filter(manifest__id=volume.id)
        #     canvasquery2 = list(canvasquery)
        #     canvaslist.append({volume.pid: canvasquery2})
        #     context['firstthumbnail'] = canvaslist
        # value = 0
        # context['value'] = value
        return context
