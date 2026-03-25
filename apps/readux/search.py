"""Search Endpoint(s)"""
from itertools import groupby
import re
from django.http import JsonResponse
from django.views import View
from elasticsearch_dsl import Q
from more_itertools import flatten

from apps.iiif.manifests.documents import ManifestDocument
from apps.readux.documents import UserAnnotationDocument
from apps.readux.templatetags.readux_extras import has_inner_hits, group_by_canvas


class SearchManifestCanvas(View):
    """
    Endpoint for text search of manifest
    :rtype json
    """

    # regex to match exact search terms in doublequotes
    re_exact_match = re.compile(r'\B(".+?")\B')

    def get_queryresults(self):
        """
        Build query results.
        :return: [description]
        :rtype: JSON
        """
        # get search params
        volume_pid = self.request.GET.get("volume_id") or ""
        canvas_pid = self.request.GET.get("canvas_id") or ""
        search_query = self.request.GET.get("keyword") or ""

        # find exact match queries (words or phrases in double quotes)
        exact_queries = self.re_exact_match.findall(search_query)
        # remove exact queries from the original search query to search separately
        search_query = re.sub(self.re_exact_match, "", search_query).strip()

        # set up elasticsearch queries for searching the volume full text
        vol_queries = []
        vol_queries_exact = []

        # techcnically we are using the search for all volumes here,
        # but we are filtering to only one volume and then getting inner hits
        volumes = ManifestDocument.search()
        # filter to only volume matching pid
        volumes = volumes.filter("term", pid=volume_pid)

        # build query for nested fields (i.e. canvas position and text)
        nested_kwargs = {
            "path": "canvas_set",
            "score_mode": "sum",
        }
        inner_hits_dict = {
            "size": 100,  # max number of pages shown in full-text results
            "highlight": {"fields": {"canvas_set.result": {}}},
        }

        # get nested inner hits on canvas (for partial match portion of query)
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
        vol_queries.append(nested_query)

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
            vol_queries_exact.append({"bool": {"should": [nested_exact]}})

        # combine exact and partial with bool: { should, must }
        q = Q("bool", should=vol_queries, must=vol_queries_exact)
        volumes = volumes.query(q)

        # execute the search
        response = volumes.execute()

        # group inner hits by canvas and collect highlighted context
        volume_matches = []
        total_matches_on_canvas = 0
        total_matches_in_volume = 0
        if int(response.hits.total.value):
            volume = response.hits[0]
            if has_inner_hits(volume):
                for canvas in group_by_canvas(volume.meta.inner_hits, limit=100):
                    volume_matches.append(
                        {
                            "canvas_index": canvas["position"],
                            "canvas_match_count": len(canvas["highlights"]),
                            "canvas_pid": canvas["pid"],
                            "context": canvas["highlights"],
                        }
                    )
                    total_matches_in_volume += len(canvas["highlights"])
                    if canvas_pid and canvas["pid"] == canvas_pid:
                        total_matches_on_canvas = len(canvas["highlights"])

        # JSON-serializable results
        results = {
            "matches_in_text": {
                "total_matches_on_canvas": total_matches_on_canvas,
                "total_matches_in_volume": total_matches_in_volume,
                "volume_matches": volume_matches,
            }
        }

        # ------------------------------------------------------------
        # Now, search for UserAnnotations
        annotations = UserAnnotationDocument.search()

        # filter to only owner matching user, volume matching pid
        annotations = annotations.filter(
            "term", owner_username=self.request.user.username
        ).filter("term", manifest_pid=volume_pid)

        # search for partial matches
        anno_queries = [Q("multi_match", query=search_query, fields=["content"])]

        # search for exact matches
        anno_queries_exact = []
        for i, exq in enumerate(exact_queries):
            # separate exact searches so we can put them in "must" boolean query
            eq = exq.replace('"', "").strip()
            nested_exact = Q("multi_match", query=eq, fields=["content"], type="phrase")
            anno_queries_exact.append({"bool": {"should": [nested_exact]}})

        # combine exact and partial with bool: { should, must }
        q = Q("bool", should=anno_queries, must=anno_queries_exact)
        annotations = annotations.query(q)
        annotations = annotations.highlight("content")

        # execute the search
        anno_response = annotations.execute()

        # collect metadata and highlighted context from hits
        annotation_match_count = int(anno_response.hits.total.value)
        annotation_matches = []
        if annotation_match_count:
            for anno in anno_response.hits:
                annotation_matches.append(
                    {
                        "canvas_index": anno["canvas_index"],
                        "canvas_pid": anno["canvas_pid"],
                        "context": list(anno.meta.highlight.content),
                    }
                )

        # group annotations by canvas pid
        # TODO: is there a way to do this without iterating over the same data multiple times?
        # maybe some kind of aggregation in elastic?
        group_key = lambda a: a["canvas_pid"]
        annotation_matches.sort(key=group_key)
        annotation_matches_grouped = []
        annotation_matches_on_canvas = 0
        annotation_matches_in_volume = 0
        for k, v in groupby(annotation_matches, key=group_key):
            canvas_matches = list(flatten([match["context"] for match in v]))
            annotation_matches_grouped.append(
                {
                    "canvas_index": anno["canvas_index"],
                    "canvas_match_count": len(canvas_matches),
                    "canvas_pid": k,
                    "context": canvas_matches,
                }
            )
            annotation_matches_in_volume += len(canvas_matches)
            if canvas_pid and k == canvas_pid:
                annotation_matches_on_canvas = len(canvas_matches)

        results["matches_in_annotations"] = {
            "total_matches_on_canvas": annotation_matches_on_canvas,
            "total_matches_in_volume": annotation_matches_in_volume,
            "volume_matches": annotation_matches_grouped,
        }

        return results

    def get(self, request, *args, **kwargs):  # pylint: disable = unused-argument
        """
        Respond to GET requests for search queries.
        :rtype: JsonResponse
        """
        return JsonResponse(status=200, data=self.get_queryresults())
