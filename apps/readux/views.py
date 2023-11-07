"""Django Views for the Readux app"""
import re
from os import path
from urllib.parse import urlencode
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormMixin
from django.contrib.sitemaps import Sitemap
from django.db.models import Max, Count
from django.urls import reverse
from elasticsearch_dsl import Q, NestedFacet, TermsFacet
from elasticsearch_dsl.query import MultiMatch
import config.settings.local as settings
from apps.iiif.manifests.documents import ManifestDocument
from apps.readux.forms import ManifestSearchForm
from apps.export.export import JekyllSiteExport
from apps.export.forms import JekyllExportForm
from .models import UserAnnotation
from ..cms.models import Page, CollectionsPage, VolumesPage
from ..iiif.kollections.models import Collection
from ..iiif.canvases.models import Canvas
from ..iiif.manifests.models import Manifest

SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
ORDER_OPTIONS = ['asc', 'desc']

class CollectionsList(ListView):
    """Django List View for :class:`apps.iiif.kollections.models.Collection`s"""
    template_name = "collections.html"

    context_object_name = 'collections'
    queryset = Collection.objects.all()

class VolumesList(ListView):
    """Django List View for :class:`apps.iiif.manifests.models.Manifest`s"""
    template_name = "volumes.html"
    SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
    ORDER_OPTIONS = ['asc', 'desc']
    context_object_name = 'volumes'

    def get_queryset(self):
        return Manifest.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)

        q = self.get_queryset()

        if sort not in SORT_OPTIONS:
            sort = 'title'
        if order not in ORDER_OPTIONS:
            order = 'asc'

        if sort == 'title':
            if order == 'asc':
                q = q.order_by('label')
            elif order == 'desc':
                q = q.order_by('-label')
        elif sort == 'author':
            if order == 'asc':
                q = q.order_by('author')
            elif order == 'desc':
                q = q.order_by('-author')
        elif sort == 'date published':
            if order == 'asc':
                q = q.order_by('published_date_edtf')
            elif order == 'desc':
                q = q.order_by('-published_date_edtf')
        elif sort == 'date added':
            if order == 'asc':
                q = q.order_by('created_at')
            elif order == 'desc':
                q = q.order_by('-created_at')

        sort_url_params = {'sort': sort, 'order': order}
        order_url_params = {'sort': sort, 'order': order}
        if 'sort' in sort_url_params:
            del sort_url_params['sort']

        context['volumes'] = q.all
        context.update({
            'sort_url_params': urlencode(sort_url_params),
            'order_url_params': urlencode(order_url_params),
            'sort': sort, 'SORT_OPTIONS': SORT_OPTIONS,
            'order': order, 'ORDER_OPTIONS': ORDER_OPTIONS,
        })
        return context

class CollectionDetail(ListView):
    """Django Template View for a :class:`apps.iiif.kollections.models.Collection`"""
    template_name = "collection.html"
    SORT_OPTIONS = ['title', 'author', 'date published', 'date added']
    ORDER_OPTIONS = ['asc', 'desc']
    paginate_by = 10

    def get_queryset(self):
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)
        q = Collection.objects.filter(pid=self.kwargs['collection']).first().manifests.all()

        if sort is None:
            sort = 'title'
        if order is None:
            order = 'asc'

        if sort == 'title':
            if order == 'asc':
                q = q.order_by('label')
            elif order == 'desc':
                q = q.order_by('-label')
        elif sort == 'author':
            if order == 'asc':
                q = q.order_by('author')
            elif order == 'desc':
                q = q.order_by('-author')
        elif sort == 'date published':
            if order == 'asc':
                q = q.order_by('published_date_edtf')
            elif order == 'desc':
                q = q.order_by('-published_date_edtf')
        elif sort == 'date added':
            if order == 'asc':
                q = q.order_by('created_at')
            elif order == 'desc':
                q = q.order_by('-created_at')

        return 	q

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort = self.request.GET.get('sort', None)
        order = self.request.GET.get('order', None)

        q = Collection.objects.filter(pid=self.kwargs['collection']).first().manifests

        if sort is None:
            sort = 'title'
        if order is None:
            order = 'asc'

        if sort == 'title':
            if order == 'asc':
                q = q.order_by('label')
            elif order == 'desc':
                q = q.order_by('-label')
        elif sort == 'author':
            if order == 'asc':
                q = q.order_by('author')
            elif order == 'desc':
                q = q.order_by('-author')
        elif sort == 'date published':
            if order == 'asc':
                q = q.order_by('published_date_edtf')
            elif order == 'desc':
                q = q.order_by('-published_date_edtf')
        elif sort == 'date added':
            if order == 'asc':
                q = q.order_by('created_at')
            elif order == 'desc':
                q = q.order_by('-created_at')

        sort_url_params = self.request.GET.copy()
        order_url_params = self.request.GET.copy()
#         if 'sort' in sort_url_params:
#             del sort_url_params['sort']

        context['collectionlink'] = Page.objects.type(CollectionsPage).first()
        context['collection'] = Collection.objects.filter(pid=self.kwargs['collection']).first()
        context['volumes'] = q.all
        context['manifest_query_set'] = q
        context['user_annotation'] = UserAnnotation.objects.filter(owner_id=self.request.user.id)
        value = 0
        context['value'] = value
        context.update({
            'sort_url_params': urlencode(sort_url_params),
            'order_url_params': urlencode(order_url_params),
            'sort': sort, 'SORT_OPTIONS': SORT_OPTIONS,
            'order': order, 'ORDER_OPTIONS': ORDER_OPTIONS,
        })
        return context

class VolumeDetail(TemplateView):
    """Django Template View for :class:`apps.iiif.manifest.models.Manifest`"""
    template_name = "volume.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context

# FIXME: What is this used for? The template does not exist.
class AnnotationsCount(TemplateView):
    """Django Template View for :class:`apps.readux.models.UserAnnotation`"""
    template_name = "count.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        context['page'] = canvas
        manifest = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['volume'] = manifest
        context['user_annotation_page_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__id=canvas.id
        ).count()
        context['user_annotation_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__manifest__id=manifest.id
        ).count()
        return context

class PageDetail(TemplateView):
    """Django Template View for :class:`apps.iiif.canvases.models.Canvas`"""
    template_name = "page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manifest = Manifest.objects.get(pid=kwargs['volume'])
        if 'page' in kwargs:
            canvas = Canvas.objects.filter(pid=kwargs['page']).first()
        else:
            canvas = manifest.canvas_set.all().first()
        # if 'page' in kwargs and kwargs['page'] == 'all':
        #     context['all'] = True
        context['page'] = canvas
        context['volume'] = manifest
        context['pagelink'] = manifest.image_server
        context['collectionlink'] = Page.objects.type(CollectionsPage).first()
        context['volumelink'] = Page.objects.type(VolumesPage).first()
        context['user_annotation_page_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__id=canvas.id
        ).count()
        context['user_annotation_count'] = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__manifest__id=manifest.id
        ).count()
        context['mirador_url'] = settings.MIRADOR_URL

        user_annotation_index = UserAnnotation.objects.all()

        user_annotation_index = user_annotation_index.filter(canvas__manifest__label=manifest.label)

        user_annotation_index = user_annotation_index.filter(owner_id=self.request.user.id).distinct()

        user_annotation_index = user_annotation_index.values(
                 'canvas__position',
                 'canvas__manifest__label',
                 'canvas__pid'
             ).annotate(
                 Count(
                     'canvas__position')
                 ).order_by('canvas__position')

        context['user_annotation_index'] = user_annotation_index
        context['json_data'] = {'json_data': list(user_annotation_index)}

        return context

class ExportOptions(TemplateView, FormMixin):
    """Django Template View for Export"""
    template_name = "export.html"
    form_class = JekyllExportForm

    def get_form_kwargs(self):
        # keyword arguments needed to initialize the form
        kwargs = super(ExportOptions, self).get_form_kwargs()
        # add user, which is used to determine available groups
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        context['export_form'] = self.get_form()
        return context

class ExportDownload(TemplateView):
    """Django Template View for downloading an export."""
    template_name = "export_download.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        filename = kwargs['filename']
        context['filename'] = filename
        # check to see if the file exists
        if path.exists(JekyllSiteExport.get_zip_path(filename)):
            context['file_exists'] = True
        else:
            context['file_exists'] = False

        return context

class ExportDownloadZip(View):
    """Django View for downloading the zipped up export."""
    def get(self, request, *args, **kwargs):
        """[summary]

        :param View: [description]
        :type View: [type]
        :param request: [description]
        :type request: [type]
        :return: [description]
        :rtype: [type]
        """
        jekyll_export = JekyllSiteExport(None, "v2", github_repo=None, deep_zoom=False, owners=[self.request.user.id], user=self.request.user);
        zip = jekyll_export.get_zip_file(kwargs['filename'])
        resp = HttpResponse(zip, content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=jekyll_site_export.zip'
        return resp

class VolumeSearchView(ListView, FormMixin):
    """View to search across all volumes with Elasticsearch"""
    model = Manifest
    form_class = ManifestSearchForm
    template_name = "search_results.html"
    context_object_name = "volumes"
    paginate_by = 25
    # default fields to search when using query box; ^ with number indicates a boosted field
    query_search_fields = ["pid", "label^5", "summary^2", "author"]

    # Facet fields: tuples of (name, facet) where "name" matches the form field name,
    # and "facet" is an Elasticsearch facet (with field argument matching the ManifestDocument
    # field name for the desired field, and size argument accommodating all possible values)
    facets = [
        # NOTE: This size is set to accommodate all languages, of which there are 830 at present
        ("language", TermsFacet(field="languages", size=1000, min_doc_count=1)),
        # TODO: Determine a good size for authors or consider alternate approach (i.e. not faceted)
        ("author", TermsFacet(field="authors", size=2000, min_doc_count=1)),
        ("collection", NestedFacet("collections", TermsFacet(field="collections.label", size=2000, min_doc_count=1)))
    ]
    defaults = {
        "sort": "label_alphabetical"
    }

    # regex to match terms in doublequotes
    re_exact_match = re.compile(r'\B(".+?")\B')

    def get_form_kwargs(self):
        # adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/
        kwargs = super().get_form_kwargs()
        # use GET for form data so that query params appear in URL
        form_data = self.request.GET.copy()

        # sort by form choice
        if "sort" in form_data and bool(form_data.get("sort")):
            form_data["sort"] = form_data.get("sort")
        # by default, if there is a search query, sort by relevance
        elif form_data.get("q"):
            form_data["sort"] = "_score"
        # by default, if sort is an empty string, sort by specified default
        elif "sort" in form_data:
            form_data["sort"] = self.defaults["sort"]

        # set defaults for all form values
        for key, val in self.defaults.items():
            form_data.setdefault(key, val)

        kwargs["data"] = form_data
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        volumes_response = self.get_queryset().execute()
        # populate a dict with "buckets" of extant categories for each facet
        facets = {}
        for (facet, _) in self.facets:
            if hasattr(volumes_response.aggregations, facet):
                aggs = getattr(volumes_response.aggregations, facet)
                # use "inner" to handle NestedFacet
                if hasattr(aggs, "inner"):
                    aggs = getattr(aggs, "inner")
                facets.update({
                    # get buckets array from each facet in the aggregations dict
                    facet: getattr(aggs, "buckets"),
                })
        context_data["form"].set_facets(facets)

        # get min and max date aggregations and set on form
        if hasattr(volumes_response.aggregations, "min_date"):
            min_date = getattr(volumes_response.aggregations, "min_date")
            if hasattr(volumes_response.aggregations, "max_date"):
                max_date = getattr(volumes_response.aggregations, "max_date")
                if hasattr(
                    min_date, "value_as_string"
                ) and hasattr(
                    max_date, "value_as_string"
                ):
                    context_data["form"].set_date(
                        getattr(min_date, "value_as_string"),
                        getattr(max_date, "value_as_string"),
                    )

        return context_data

    def get_queryset(self):
        form = self.get_form()
        volumes = ManifestDocument.search()

        if not form.is_valid():
            # empty result on invalid form
            return volumes.filter("match_none")
        form_data = form.cleaned_data

        # default to empty string if no query in form data
        search_query = form_data.get("q") or ""
        scope = form_data.get("scope") or "all"
        if search_query:
            # find exact match queries (words or phrases in double quotes)
            exact_queries = self.re_exact_match.findall(search_query)
            # remove exact queries from the original search query to search separately
            search_query = re.sub(self.re_exact_match , "", search_query).strip()

            es_queries = []
            es_queries_exact = []
            if scope in ["all", "metadata"]:
                # query for root level fields
                if search_query:
                    multimatch_query = Q(
                        "multi_match", query=search_query, fields=self.query_search_fields
                    )
                    es_queries.append(multimatch_query)
                for exq in exact_queries:
                    # separate exact searches so we can put them in "must" boolean query
                    multimatch_exact = Q(
                        "multi_match",
                        query=exq.replace('"', "").strip(),  # strip double quotes
                        fields=self.query_search_fields,
                        type="phrase",  # type = "phrase" for exact phrase matches
                    )
                    es_queries_exact.append({"bool": {"should": [multimatch_exact]}})

            if scope in ["all", "text"]:
                # query for nested fields (i.e. canvas position and text)
                nested_kwargs = {
                    "path": "canvas_set",
                    # sum scores if in full text only search, so vols with most hits show up first.
                    # if also searching metadata, use avg (default) instead, to not over-inflate.
                    "score_mode": "sum" if scope == "text" else "avg",
                }
                inner_hits_dict = {
                    "size": 3,  # max number of pages shown in full-text results
                    "highlight": {"fields": {"canvas_set.result": {}}},
                }
                if search_query:
                    nested_query = Q(
                        "nested",
                        query=Q(
                            "multi_match",
                            query=search_query,
                            fields=["canvas_set.result"],
                        ),
                        inner_hits={ **inner_hits_dict, "name": "canvases" },
                        **nested_kwargs,
                    )
                    es_queries.append(nested_query)
                for i, exq in enumerate(exact_queries):
                    # separate exact searches so we can put them in "must" boolean query
                    nested_exact = Q(
                        "nested",
                        query=Q(
                            "multi_match",
                            query=exq.replace('"', "").strip(),
                            fields=["canvas_set.result"],
                            type="phrase",
                        ),
                        # each inner_hits set needs to have a different name in elasticsearch
                        inner_hits={ **inner_hits_dict, "name": f"canvases_{i}" },
                        **nested_kwargs,
                    )
                    es_queries_exact[i]["bool"]["should"].append(nested_exact)

            # combine them with bool: { should, must }
            q = Q("bool", should=es_queries, must=es_queries_exact)
            volumes = volumes.query(q)

        # highlight
        volumes = volumes.highlight_options(
            require_field_match=False,
            fragment_size=200,
            number_of_fragments=10,
            max_analyzed_offset=999999,
        ).highlight(
            "label", "author", "summary"
        )

        # filter on authors
        author_filter = form_data.get("author") or ""
        if author_filter:
            volumes = volumes.filter("terms", authors=author_filter)

        # filter on languages
        language_filter = form_data.get("language") or ""
        if language_filter:
            volumes = volumes.filter("terms", languages=language_filter)

        # filter on collections
        collection_filter = form_data.get("collection") or ""
        if collection_filter:
            volumes = volumes.filter("nested", path="collections", query=Q(
                "terms", **{"collections.label": collection_filter}
            ))

        # filter on date published
        min_date_filter = form_data.get("start_date") or ""
        if min_date_filter:
            volumes = volumes.filter("range", date_earliest={"gte": min_date_filter})
        max_date_filter = form_data.get("end_date") or ""
        if max_date_filter:
            volumes = volumes.filter("range", date_latest={"lte": max_date_filter})

        # create aggregation buckets for facet fields
        for (facet_name, facet) in self.facets:
            volumes.aggs.bucket(facet_name, facet.get_aggregation())

        # get min and max date published values
        volumes.aggs.metric("min_date", "min", field="date_earliest")
        volumes.aggs.metric("max_date", "max", field="date_latest")

        # sort
        volumes = volumes.sort(form_data["sort"])

        # return elasticsearch_dsl Search instance
        return volumes


class ManifestsSitemap(Sitemap):
    """Django Sitemap for Manafests"""
    limit = 5
    # priority unknown
    def items(self):
        return Manifest.objects.all()

    def location(self, item):
        return reverse('volumeall', kwargs={'volume': item.pid})

    def lastmod(self, item):
        return item.updated_at

class CollectionsSitemap(Sitemap):
    """Django Sitemap for Collections"""
    # priority unknown
    def items(self):
        return Collection.objects.all()

    def location(self, item):
        return reverse('collection', kwargs={'collection': item.pid})

    def lastmod(self, item):
        return item.updated_at
