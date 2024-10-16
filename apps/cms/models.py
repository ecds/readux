"""CMS Models."""
from modelcluster.fields import ParentalManyToManyField
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtailautocomplete.edit_handlers import AutocompletePanel
from django.db import models
from apps.cms.blocks import BaseStreamBlock
from apps.readux.forms import AllCollectionsForm, AllVolumesForm
from apps.readux.models import UserAnnotation
from apps.iiif.kollections.models import Collection
from apps.iiif.manifests.models import Manifest
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
    collections = Collection.objects.all()
    volumes = Manifest.objects.all()
    content_panels = Page.content_panels + [
        FieldPanel('page_title', classname="full"),
        FieldPanel('tagline', classname="full"),
        FieldPanel('paragraph', classname="full"),
        FieldPanel('layout', classname="full"),
    ]
    initial = {"sort": "title", "order": "asc", "display": "grid"}
    sort_fields = {
        "title": "label",
        "added": "created_at",
        "volumes": "volumes_count",
    }

    def get_form(self, request):
        """Get the form for setting sort and order"""
        # use GET instead of default POST/PUT for form data
        form_data = request.GET.copy()

        # sort by chosen sort
        if "sort" in form_data and bool(form_data.get("sort")):
            form_data["sort"] = form_data.get("sort")

        # Otherwise set all form values to default
        for key, val in self.initial.items():
            form_data.setdefault(key, val)

        return AllCollectionsForm(data=form_data)

    def get_queryset(self, form, queryset):
        """Get the sorted set of objects to display"""

        # return empty queryset if not valid
        if not form.is_valid():
            return queryset.none()

        # get sort and order selections from form
        search_opts = form.cleaned_data
        sort = search_opts.get("sort", "title")
        if sort not in self.sort_fields:
            sort = "title"
        order = search_opts.get("order", "asc")
        sign = "-" if order == "desc" else ""

        # include volume count in queryset if sort 
        if "volumes" in sort:
            queryset = queryset.annotate(volumes_count=models.Count("manifests"))

        # build order_by query to sort results
        queryset = queryset.order_by(f"{sign}{self.sort_fields[sort]}")

        return queryset

    def get_context(self, request):
        """Context function."""
        context = super().get_context(request)

        form = self.get_form(request)
        query_set = self.get_queryset(form, self.collections)

        paginator = Paginator(query_set, 8) # Show 8 collections per page

        page = request.GET.get("page", 1)
        try:
            collections = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            collections = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page = paginator.num_pages
            collections = paginator.page(page)

        context.update({
            "form": form,
            "collections": collections,
            "paginator_range": paginator.get_elided_page_range(page, on_each_side=2),
        })

        return context

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
    initial = {"sort": "title", "order": "asc", "display": "grid"}
    sort_fields = {
        "title": "label",
        "author": "author",
        "date": "date_sort_ascending",
        "added": "created_at",
    }

    def get_form(self, request):
        """Get the form for setting sort and order"""
        # use GET instead of default POST/PUT for form data
        form_data = request.GET.copy()

        # sort by chosen sort
        if "sort" in form_data and bool(form_data.get("sort")):
            form_data["sort"] = form_data.get("sort")

        # Otherwise set all form values to default
        for key, val in self.initial.items():
            form_data.setdefault(key, val)

        return AllVolumesForm(data=form_data)

    def get_queryset(self, form, queryset):
        """Get the sorted set of objects to display"""

        # return empty queryset if not valid
        if not form.is_valid():
            return queryset.none()

        # get sort and order selections from form
        search_opts = form.cleaned_data
        sort = search_opts.get("sort", "title")
        if sort not in self.sort_fields:
            sort = "title"
        order = search_opts.get("order", "asc")
        sign = "-" if order == "desc" else ""

        # build order_by query to sort results
        if sort == "date" and order == "desc":
            # special case for date, descending: need to use date_sort_descending field
            # and sort nulls last
            queryset = queryset.order_by(models.F("date_sort_descending").desc(nulls_last=True))
        else:
            queryset = queryset.order_by(f"{sign}{self.sort_fields[sort]}")

        return queryset

    def get_context(self, request):
        """Context function."""
        context = super().get_context(request)

        form = self.get_form(request)
        query_set = self.get_queryset(form, self.volumes)

        paginator = Paginator(query_set, 8) # Show 8 volumes per page

        page = request.GET.get("page", 1)
        try:
            volumes = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            volumes = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page = paginator.num_pages
            volumes = paginator.page(page)

        context.update({
            "form": form,
            "volumes": volumes,
            "user_annotation": UserAnnotation.objects.filter(owner_id=request.user.id),
            "paginator_range": paginator.get_elided_page_range(page, on_each_side=2),
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

    background_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Optional background image for the site header",
    )

    featured_story_title = models.CharField(
        help_text="Title of the featured story", blank=True, max_length=255
    )
    featured_story_summary = models.TextField(
        help_text="A summary or excerpt of the featured story", blank=True
    )
    featured_story_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Thumbnail image for the featured story",
    )
    featured_story_url = models.URLField(
        help_text="Link to the featured story", blank=True
    )
    featured_video_url = models.URLField(
        help_text="Vimeo link to the featured video (e.g. https://vimeo.com/76979871, only Vimeo supported)", blank=True
    )
    featured_video_title = models.CharField(
        help_text="Title of the featured video", blank=True, max_length=255
    )
    featured_video_tagline = models.CharField(
        help_text="A short description or tagline for the featured video", blank=True, max_length=255
    )

    content_panels = Page.content_panels + [
        FieldPanel('tagline', classname="full"),
        FieldPanel('background_image', classname="full"),
        FieldPanel('content_display', classname="full"),
        AutocompletePanel('featured_collections', target_model="kollections.Collection"),
        FieldPanel('featured_collections_sort_order', classname="full"),
        AutocompletePanel('featured_volumes', target_model="manifests.Manifest"),
        FieldPanel('featured_volumes_sort_order', classname="full"),
        MultiFieldPanel(children=[
            FieldPanel('featured_story_title'),
            FieldPanel('featured_story_summary'),
            FieldPanel('featured_story_image'),
            FieldPanel('featured_story_url'),
        ], heading='Featured story (optional)'),
        MultiFieldPanel(children=[
            FieldPanel('featured_video_url'),
            FieldPanel('featured_video_title'),
            FieldPanel('featured_video_tagline'),
        ], heading='Featured video (optional)'),
    ]

    def featured_volume_count(self):
        return self.featured_volumes.all().count()

    def has_featured_volume(self):
        return self.featured_volume_count() > 0

    def get_context(self, request):
        """Function that returns context"""
        context = super().get_context(request)
        context['volumesurl'] = Page.objects.type(VolumesPage).first()
        context['collectionsurl'] = Page.objects.type(CollectionsPage).first()
        return context
