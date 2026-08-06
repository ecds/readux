"""Django Views for the Readux app"""

import re
from os import path
from urllib.parse import urlencode
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.contrib.sitemaps import Sitemap
from django.db.models import Max, Count, F
from django.urls import reverse
from elasticsearch_dsl import Q, NestedFacet, TermsFacet
from elasticsearch_dsl.query import MultiMatch
from apps.utils.dates import date_to_jd, jd_to_date
from datetime import date
import config.settings.local as settings
from apps.iiif.manifests.documents import ManifestDocument
from apps.readux.forms import AllVolumesForm, ManifestSearchForm
from apps.export.export import JekyllSiteExport
from apps.export.forms import JekyllExportForm
from .models import UserAnnotation
from ..cms.models import Page, CollectionsPage, VolumesPage
from ..iiif.kollections.models import Collection
from ..iiif.canvases.models import Canvas
from ..iiif.manifests.models import Manifest
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

SORT_OPTIONS = ["title", "author", "date published", "date added"]
ORDER_OPTIONS = ["asc", "desc"]


class CollectionDetail(DetailView, FormMixin):
    """Django Template View for a :class:`apps.iiif.kollections.models.Collection`"""

    template_name = "collection.html"
    slug_field = "pid"
    slug_url_kwarg = "collection"
    form_class = AllVolumesForm
    model = Collection
    initial = {"sort": "title", "order": "asc", "display": "grid", "per_page": "60"}
    sort_fields = {
        "title": "label",
        "author": "author",
        "date": "date_sort_ascending",
        "added": "created_at",
    }

    def get_form_kwargs(self):
        """get form arguments from request and configured defaults"""
        kwargs = super().get_form_kwargs()

        # use GET instead of default POST/PUT for form data
        form_data = self.request.GET.copy()

        # set all form values to default
        for key, val in self.initial.items():
            form_data.setdefault(key, val)

        kwargs["data"] = form_data

        return kwargs

    def get_volumes(self, form=None):
        """Get the sorted set of volumes to display"""
        form = form or self.get_form()
        collection = self.get_object()
        queryset = collection.manifests.all()

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
            queryset = queryset.order_by(
                F("date_sort_descending").desc(nulls_last=True)
            )
        else:
            queryset = queryset.order_by(f"{sign}{self.sort_fields[sort]}")

        return queryset

    def get_context_data(self, **kwargs):
        """Context function."""
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        volumes = self.get_volumes(form=form)

        per_page_default = int(self.initial.get("per_page", 60))
        per_page = per_page_default
        if form.is_valid():
            try:
                per_page = int(form.cleaned_data.get("per_page") or per_page_default)
            except (TypeError, ValueError):
                per_page = per_page_default

        # add paginator manually since this isn't a ListView
        paginator = Paginator(volumes, per_page)

        page = self.request.GET.get("page", 1)
        try:
            volumes = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            volumes = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page = paginator.num_pages
            volumes = paginator.page(page)

        context.update(
            {
                "volumes": volumes,
                "form": form,
                "user_annotation": UserAnnotation.objects.filter(
                    owner_id=self.request.user.id
                ),
                "paginator_range": paginator.get_elided_page_range(
                    page, on_each_side=2
                ),
                "collectionlink": Page.objects.type(CollectionsPage).first(),
            }
        )

        return context


class VolumeDetail(TemplateView):
    """Django Template View for :class:`apps.iiif.manifest.models.Manifest`"""

    template_name = "volume.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["volume"] = Manifest.objects.filter(pid=kwargs["volume"]).first()
        return context


# FIXME: What is this used for? The template does not exist.
class AnnotationCount(TemplateView):
    """Django Template View for :class:`apps.readux.models.UserAnnotation`"""

    template_name = "count.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        canvas = Canvas.objects.filter(pid=kwargs["page"]).first()
        context["page"] = canvas
        manifest = Manifest.objects.filter(pid=kwargs["volume"]).first()
        context["volume"] = manifest
        context["user_annotation_page_count"] = (
            UserAnnotation.objects.filter(owner_id=self.request.user.id)
            .filter(canvas__id=canvas.id)
            .count()
        )
        context["user_annotation_count"] = (
            UserAnnotation.objects.filter(owner_id=self.request.user.id)
            .filter(canvas__manifest__id=manifest.id)
            .count()
        )
        return context


class PageDetail(TemplateView):
    """Django Template View for :class:`apps.iiif.canvases.models.Canvas`"""

    template_name = "page.html"

    def get_metadatum(self, volume, key):
        """Attempt to retrieve a value from a volume's metadata by key. If it cannot
        be found, return an empty string."""
        if hasattr(volume, key):
            # first try volume's model attributes
            return getattr(volume, key)
        elif isinstance(volume.metadata, dict):
            # if not a model attr, attempt to get value from volume metadata;
            # if metadata is a dict (rare), just lookup by key
            return volume.metadata.get(key, "")
        else:
            # if metadata is a list (more common / correct IIIF spec), find the matching
            # "label" attribute by key
            meta_list = list(volume.metadata)
            metadatum = filter(lambda m: m["label"] == key, meta_list)
            try:
                # filter() returns an iterator; try to retrieve the first matching entry's value
                return next(metadatum).get("value", "") if metadatum else ""
            except StopIteration:
                return ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manifest = Manifest.objects.get(pid=kwargs["volume"])
        if "page" in kwargs:
            canvas = Canvas.objects.filter(pid=kwargs["page"]).first()
        else:
            canvas = manifest.canvas_set.all().first()
        # if 'page' in kwargs and kwargs['page'] == 'all':
        #     context['all'] = True
        context["page"] = canvas
        context["volume"] = manifest
        context["pagelink"] = manifest.image_server
        context["collectionlink"] = Page.objects.type(CollectionsPage).first()
        context["volumelink"] = Page.objects.type(VolumesPage).first()
        context["user_annotation_page_count"] = (
            UserAnnotation.objects.filter(owner_id=self.request.user.id)
            .filter(canvas__id=canvas.id)
            .count()
        )
        context["user_annotation_count"] = (
            UserAnnotation.objects.filter(owner_id=self.request.user.id)
            .filter(canvas__manifest__id=manifest.id)
            .count()
        )

        user_annotation_index = UserAnnotation.objects.all()

        user_annotation_index = user_annotation_index.filter(
            canvas__manifest__label=manifest.label
        )

        user_annotation_index = user_annotation_index.filter(
            owner_id=self.request.user.id
        ).distinct()

        user_annotation_index = (
            user_annotation_index.values(
                "canvas__position", "canvas__manifest__label", "canvas__pid"
            )
            .annotate(Count("canvas__position"))
            .order_by("canvas__position")
        )

        context["user_annotation_index"] = user_annotation_index
        context["json_data"] = {"json_data": list(user_annotation_index)}

        # add custom metadata from django settings to context
        if hasattr(settings, "CUSTOM_METADATA"):
            custom_metadata = {}
            for key, metadata in settings.CUSTOM_METADATA.items():
                # Extract multi flag
                multi = metadata.get(
                    "multi", False
                )  # Default to False if not specified

                # Attempt to get this manifest's value for each key
                value = self.get_metadatum(manifest, key)
                if value:
                    custom_metadata[key] = {"value": value, "multi": multi}

            context["custom_metadata"] = custom_metadata

        return context


class ExportOptions(TemplateView, FormMixin):
    """Django Template View for Export"""

    template_name = "export.html"
    form_class = JekyllExportForm

    def get_form_kwargs(self):
        # keyword arguments needed to initialize the form
        kwargs = super(ExportOptions, self).get_form_kwargs()
        # add user, which is used to determine available groups
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["volume"] = Manifest.objects.filter(pid=kwargs["volume"]).first()
        context["export_form"] = self.get_form()
        return context


class ExportDownload(TemplateView):
    """Django Template View for downloading an export."""

    template_name = "export_download.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["volume"] = Manifest.objects.filter(pid=kwargs["volume"]).first()
        filename = kwargs["filename"]
        context["filename"] = filename
        # check to see if the file exists
        if path.exists(JekyllSiteExport.get_zip_path(filename)):
            context["file_exists"] = True
        else:
            context["file_exists"] = False

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
        jekyll_export = JekyllSiteExport(
            None,
            "v2",
            github_repo=None,
            deep_zoom=False,
            owners=[self.request.user.id],
            user=self.request.user,
        )
        zip = jekyll_export.get_zip_file(kwargs["filename"])
        resp = HttpResponse(zip, content_type="application/x-zip-compressed")
        resp["Content-Disposition"] = "attachment; filename=jekyll_site_export.zip"
        return resp


class VolumeSearchView(ListView, FormMixin):
    """View to search across all volumes with Elasticsearch"""

    model = Manifest
    form_class = ManifestSearchForm
    template_name = "search_results.html"
    context_object_name = "volumes"
    paginate_by = 20
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
        (
            "collection",
            NestedFacet(
                "collections",
                TermsFacet(field="collections.label", size=2000, min_doc_count=1),
            ),
        ),
    ]
    defaults = {"sort": "label_alphabetical", "display": "list", "per_page": "60"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pull additional facets from Elasticsearch
        if (
            settings
            and hasattr(settings, "CUSTOM_METADATA")
            and isinstance(settings.CUSTOM_METADATA, dict)
        ):
            for key in settings.CUSTOM_METADATA.keys():
                self.facets.append(
                    (
                        key,
                        NestedFacet(
                            "metadata",
                            TermsFacet(
                                field=f"metadata.{key}", size=2000, min_doc_count=1
                            ),
                        ),
                    )
                )

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

    def get_paginate_by(self, queryset):
        """Allow per-page size selection via form."""
        form = self.get_form()
        default_per_page = int(self.defaults.get("per_page", 20))
        if form.is_valid():
            try:
                return int(form.cleaned_data.get("per_page") or default_per_page)
            except (TypeError, ValueError):
                return default_per_page
        return default_per_page

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # add configured custom metadata keys to context data
        context_data["CUSTOM_METADATA_KEYS"] = (
            [
                # use django-friendly form field names
                key.casefold().replace(" ", "_")
                for key in settings.CUSTOM_METADATA.keys()
                if settings.CUSTOM_METADATA[key].get("faceted", False) == True
            ]
            if hasattr(settings, "CUSTOM_METADATA")
            and isinstance(settings.CUSTOM_METADATA, dict)
            else []
        )

        # size=0: return aggregations only — no hits, no highlighting, much faster.
        # The actual paginated hits come from the ListView machinery above.
        volumes_response = self.get_queryset()[:0].execute()
        # populate a dict with "buckets" of extant categories for each facet
        facets = {}
        for facet, _ in self.facets:
            if hasattr(volumes_response.aggregations, facet):
                aggs = getattr(volumes_response.aggregations, facet)
                # use "inner" to handle NestedFacet
                if hasattr(aggs, "inner"):
                    aggs = getattr(aggs, "inner")
                facets.update(
                    {
                        # get buckets array from each facet in the aggregations dict
                        facet: getattr(aggs, "buckets"),
                    }
                )
        context_data["form"].set_facets(facets)

        # get min and max date aggregations and set on form.
        # nested under date_range_scope.in_scope (see get_queryset) so the range
        # reflects every active filter except the date range itself, and further
        # under dated_earliest/dated_latest filter buckets so undated volumes are
        # excluded from the aggregation range.
        date_range_scope = getattr(volumes_response.aggregations, "date_range_scope", None)
        in_scope = getattr(date_range_scope, "in_scope", None) if date_range_scope else None
        dated_earliest = getattr(in_scope, "dated_earliest", None) if in_scope else None
        dated_latest = getattr(in_scope, "dated_latest", None) if in_scope else None
        context_data["date_range_has_bce"] = False
        if dated_earliest and dated_latest:
            min_date = getattr(dated_earliest, "min_date", None)
            max_date = getattr(dated_latest, "max_date", None)
            # value_as_string on a FloatField metric is the raw JD float as a string,
            # not an ISO date — convert via jd_to_date instead.
            min_jd = getattr(min_date, "value", None) if min_date else None
            max_jd = getattr(max_date, "value", None) if max_date else None
            if min_jd is not None and max_jd is not None:
                # jd_to_date returns None for pre-CE dates (year 0 / 1 BC) because
                # Python's date.MINYEAR = 1. Clamp to date(1, 1, 1) so the slider
                # has a valid lower bound; BCE volumes remain indexed and searchable.
                # Flag this on context so the template/JS can tell the user their
                # "1" option actually stands in for "1 or earlier (BCE included)".
                from datetime import date as _date
                clamped_min_d = jd_to_date(min_jd)
                context_data["date_range_has_bce"] = clamped_min_d is None
                min_d = clamped_min_d or _date(1, 1, 1)
                max_d = jd_to_date(max_jd)
                if max_d:
                    # strftime("%Y") does not zero-pad years < 1000 on all platforms,
                    # so format manually to guarantee isoparse-compatible 4-digit years.
                    def _fmt(d):
                        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
                    context_data["form"].set_date(_fmt(min_d), _fmt(max_d))

        # count of volumes with no published date at all (matching every other
        # active filter), for the "show volumes without a date" checkbox label
        undated = getattr(in_scope, "undated", None) if in_scope else None
        context_data["undated_volume_count"] = getattr(undated, "doc_count", 0) if undated else 0

        # Attach start_canvas to each volume in the current page.
        # Handle both: paginator page and raw list-like.
        vol_page = context_data.get("volumes")

        if vol_page is not None:
            # Get the underlying sequence (Paginator Page vs list)
            items = getattr(vol_page, "object_list", vol_page)

            # ES hits should have a "pid"; collect them
            pids = [getattr(v, "pid", None) for v in items if getattr(v, "pid", None)]

            if pids:
                # Two targeted queries instead of prefetch_related("canvas_set"), which
                # would load every canvas for every result just to find one per manifest.
                canvas_map = {}

                # Query 1: manifests with an explicitly marked starting page.
                # DISTINCT ON (manifest_id) returns exactly one row per manifest at the
                # DB level — no Python-side deduplication, no dirtyfields deep-copy storm.
                for c in (
                    Canvas.objects.filter(manifest__pid__in=pids, is_starting_page=True)
                    .order_by("manifest_id", "position")
                    .distinct("manifest_id")
                    .select_related("manifest")
                ):
                    canvas_map[c.manifest.pid] = c

                # Query 2: first canvas by position for the remainder
                remaining = [p for p in pids if p not in canvas_map]
                if remaining:
                    for c in (
                        Canvas.objects.filter(manifest__pid__in=remaining)
                        .order_by("manifest_id", "position")
                        .distinct("manifest_id")
                        .select_related("manifest")
                    ):
                        canvas_map[c.manifest.pid] = c

                for v in items:
                    v.start_canvas = canvas_map.get(getattr(v, "pid", None))

        return context_data

    def get_queryset(self):
        form = self.get_form()
        volumes = ManifestDocument.search()

        # canvas_set contains full OCR text for every page — potentially megabytes per volume.
        # Exclude it from _source so ES doesn't serialize and return it for every hit.
        # inner_hits (per-page match context) are fetched separately and are unaffected.
        volumes = volumes.source(excludes=["canvas_set"])

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
            search_query = re.sub(self.re_exact_match, "", search_query).strip()

            es_queries = []
            es_queries_exact = []
            if scope in ["all", "metadata"]:
                # query for root level fields
                if search_query:
                    multimatch_query = Q(
                        "multi_match",
                        query=search_query,
                        fields=self.query_search_fields,
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
                        inner_hits={**inner_hits_dict, "name": "canvases"},
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
                        inner_hits={**inner_hits_dict, "name": f"canvases_{i}"},
                        **nested_kwargs,
                    )
                    if scope == "all":
                        es_queries_exact[i]["bool"]["should"].append(nested_exact)
                    else:
                        es_queries_exact.append({"bool": {"should": [nested_exact]}})

            # combine them with bool: { should, must }
            q = Q("bool", should=es_queries, must=es_queries_exact)
            volumes = volumes.query(q)

        # highlight
        volumes = volumes.highlight_options(
            require_field_match=False,
            fragment_size=200,
            number_of_fragments=10,
            max_analyzed_offset=999999,
        ).highlight("label", "author", "summary")

        # filter on authors
        author_filter = form_data.get("author") or ""
        if author_filter:
            volumes = volumes.filter("terms", authors=author_filter)

        # filter on languages
        language_filter = form_data.get("language") or ""
        if language_filter:
            volumes = volumes.filter("terms", languages=language_filter)

        # filter on collections
        collection_filter = form_data.get("collection")
        if collection_filter:
            volumes = volumes.filter(
                "nested",
                path="collections",
                query=Q("terms", **{"collections.label": collection_filter}),
            )

        # Capture the query/filter state *before* the date-range filter below is
        # applied — Elasticsearch scopes all non-global aggregations by the final
        # request's full query+filter body, regardless of the Python call order
        # used to build it, so simply adding the aggs earlier doesn't exempt them
        # from a date filter added later. Reusing this captured query inside a
        # "global" aggregation (which ignores query context entirely on its own)
        # is what actually lets the min/max date aggregation reflect the full
        # available range — respecting every other active filter (search terms,
        # author, language, collection) but not the date range filter itself —
        # so a "reset to full range" control has something real to reset to.
        pre_date_query = volumes.to_dict().get("query", {"match_all": {}})

        # filter on date published
        # Date range overlap logic: include a document if its date window overlaps the
        # filter window. A document [earliest, latest] overlaps [start, end] when:
        #   latest >= start  AND  earliest <= end
        # Using the opposite bound for each filter handles null bounds gracefully —
        # if date_earliest is null we can't exclude the document from an end_date filter,
        # and if date_latest is null we can't confirm it falls after a start_date.
        min_date_filter = form_data.get("start_date")
        max_date_filter = form_data.get("end_date") or ""
        if min_date_filter or max_date_filter:
            date_range_clauses = []
            if min_date_filter:
                min_jd = date_to_jd(date(min_date_filter.year, 1, 1))
                date_range_clauses.append(Q("exists", field="date_latest"))
                date_range_clauses.append(Q("range", date_latest={"gte": min_jd}))
            if max_date_filter:
                max_jd = date_to_jd(date(max_date_filter.year, 12, 31))
                date_range_clauses.append(Q("exists", field="date_earliest"))
                date_range_clauses.append(Q("range", date_earliest={"lte": max_jd}))
            date_range_query = Q("bool", must=date_range_clauses)

            if form_data.get("include_undated"):
                # let volumes with no date at all through too, alongside anything
                # that actually overlaps the selected range
                undated_query = Q(
                    "bool",
                    must_not=[
                        Q("exists", field="date_earliest"),
                        Q("exists", field="date_latest"),
                    ],
                )
                volumes = volumes.filter(
                    Q("bool", should=[date_range_query, undated_query], minimum_should_match=1)
                )
            else:
                volumes = volumes.filter(date_range_query)

        # filter on custom metadata fields
        if hasattr(settings, "CUSTOM_METADATA") and isinstance(
            settings.CUSTOM_METADATA, dict
        ):
            for key in [
                k
                for k in settings.CUSTOM_METADATA.keys()
                if settings.CUSTOM_METADATA[k].get("faceted", False)
            ]:
                field_name = key.casefold().replace(" ", "_")
                meta_filter = form_data.get(field_name) or ""
                if meta_filter:
                    volumes = volumes.filter(
                        "nested",
                        path="metadata",
                        query=Q("terms", **{f"metadata.{key}": meta_filter}),
                    )

        # create aggregation buckets for facet fields
        for facet_name, facet in self.facets:
            volumes.aggs.bucket(facet_name, facet.get_aggregation())

        # get min and max date published values, excluding volumes with no dates.
        # Wrapped in a "global" bucket so it ignores the query context entirely,
        # then re-scoped via `pre_date_query` (captured above) to respect every
        # other active filter except the date range itself. See the comment
        # above `pre_date_query` for why this can't just be plain aggs.
        volumes.aggs.bucket("date_range_scope", "global").bucket(
            "in_scope", "filter", filter=pre_date_query
        )
        in_scope_aggs = volumes.aggs["date_range_scope"]["in_scope"]
        in_scope_aggs.bucket(
            "dated_earliest", "filter", filter={"exists": {"field": "date_earliest"}}
        ).metric("min_date", "min", field="date_earliest")
        in_scope_aggs.bucket(
            "dated_latest", "filter", filter={"exists": {"field": "date_latest"}}
        ).metric("max_date", "max", field="date_latest")
        # count of volumes with no published date at all, matching every other
        # active filter — powers the "N volumes without a published date" label
        in_scope_aggs.bucket(
            "undated",
            "filter",
            filter={
                "bool": {
                    "must_not": [
                        {"exists": {"field": "date_earliest"}},
                        {"exists": {"field": "date_latest"}},
                    ]
                }
            },
        )

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
        return reverse("volumeall", kwargs={"volume": item.pid})

    def lastmod(self, item):
        return item.updated_at


class CollectionsSitemap(Sitemap):
    """Django Sitemap for Collections"""

    # priority unknown
    def items(self):
        return Collection.objects.all()

    def location(self, item):
        return reverse("collection", kwargs={"collection": item.pid})

    def lastmod(self, item):
        return item.updated_at
