"""CMS Models."""
from urllib.parse import urlencode
from modelcluster.fields import ParentalManyToManyField
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
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
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )

    content_panels = Page.content_panels + [
        StreamFieldPanel('body'),
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

class VolumesPage(Page):
    """Content page"""
    page_title = models.TextField(blank=True)
    tagline = models.TextField(blank=True)
    paragraph = models.TextField(blank=True)
    layout = models.CharField(
        max_length=20,
        choices=(
            ("Grid", "Grid"),
            ("List", "List"),
        ),
        default="Grid",
        help_text="Select to show all volumes as a list or a grid of icons."
    )
    collections = Collection.objects.all
    volumes = Manifest.objects.all()
    content_panels = Page.content_panels + [
        FieldPanel('page_title', classname="full"),
        FieldPanel('tagline', classname="full"),
        FieldPanel('paragraph', classname="full"),
        FieldPanel('layout', classname="full"),
    ]

    def get_context(self, request):
        """Context function."""
        context = super().get_context(request)
        sort = request.GET.get('sort', None)
        order = request.GET.get('order', None)
        query_set = self.volumes


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
            if order == 'asc':
                query_set = query_set.order_by('label')
            elif order == 'desc':
                query_set = query_set.order_by('-label')
        elif sort == 'author':
            if order == 'asc':
                query_set = query_set.order_by('author')
            elif order == 'desc':
                query_set = query_set.order_by('-author')
        elif sort == 'date published':
            if order == 'asc':
                query_set = query_set.order_by('published_date')
            elif order == 'desc':
                query_set = query_set.order_by('-published_date')
        elif sort == 'date added':
            if order == 'asc':
                query_set = query_set.order_by('created_at')
            elif order == 'desc':
                query_set = query_set.order_by('-created_at')

        sort_url_params = request.GET.copy()
        order_url_params = request.GET.copy()
        if 'sort' in sort_url_params and 'order' in order_url_params:
            del sort_url_params['sort']
            del order_url_params['order']
        elif 'sort' in sort_url_params:
            del sort_url_params['sort']
        elif 'order' in order_url_params:
            del order_url_params['order']

        paginator = Paginator(query_set, 10) # Show 10 volumes per page

        page = request.GET.get('page')
        try:
            volumes = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            volumes = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            volumes = paginator.page(paginator.num_pages)

        # make the variable 'volumes' available on the template
        context['volumes'] = volumes
#        context['volumespage'] = query_set.all
        context['user_annotation'] = UserAnnotation.objects.filter(owner_id=request.user.id)
        # annocount_list = []
        # canvaslist = []
        # for volume in query_set:
        #     user_annotation_count = UserAnnotation.objects.filter(owner_id=request.user.id).filter(canvas__manifest__id=volume.id).count()
            # annocount_list.append({volume.pid: user_annotation_count})
            # context['user_annotation_count'] = annocount_list
        #     canvasquery = Canvas.objects.filter(is_starting_page=1).filter(manifest__id=volume.id)
        #     canvasquery2 = list(canvasquery)
        #     canvaslist.append({volume.pid: canvasquery2})
        #     context['firstthumbnail'] = canvaslist
        # value = 0
        # context['value'] = value

        context.update({
            'sort_url_params': urlencode(sort_url_params),
            'order_url_params': urlencode(order_url_params),
            'sort': sort, 'sort_options': sort_options,
            'order': order, 'order_options': order_options,
        })
        return context


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
        context['volumesurl'] = Page.objects.type(VolumesPage).first()
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
