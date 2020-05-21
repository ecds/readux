"""Search Endpoint(s)"""
import json
import logging
from django.http import JsonResponse
from django.views import View
from django.db.models import Count, Q
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from ..iiif.manifests.models import Manifest
from ..iiif.canvases.models import Canvas
from ..iiif.annotations.models import Annotation
from .models import UserAnnotation

LOGGER = logging.getLogger(__name__)

class SearchManifestCanvas(View):
    """
    Endpoint for text search of manifest
    :rtype json
    """
    def get_queryresults(self):
        """
        Build query results.

        :return: [description]
        :rtype: JSON
        """
        manifest = Manifest.objects.get(pid=self.request.GET['volume'])
        # if 'page' in self.request.GET:
        #     canvas = Canvas.objects.filter(pid=self.request.GET['page']).first()
        # else:
        #     canvas = manifest.canvas_set.all().first()
        annotations = Annotation.objects.filter(
            canvas__manifest__label=manifest.label
        )
        user_annotations = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__manifest__label=manifest.label
        )
        fuzzy_search = Q()
        query = SearchQuery('')
        vector = SearchVector('content')
        # search_string = self.request.GET['q']
        search_type = self.request.GET['type']
        search_strings = self.request.GET['query'].split()
        results = {
            'search_terms': search_strings,
            'ocr_annotations': [],
            'user_annotations': []
        }

        try:
            # TODO: Write tests after rewrite.
            if search_strings:
                if search_type == 'partial':
                    for search_string in search_strings:
                        query = query | SearchQuery(search_string)
                        fuzzy_search |= Q(content__icontains=search_string) ##
                    annotations = annotations.filter(fuzzy_search)
                    user_annotations = user_annotations.filter(fuzzy_search)
                else:
                    for search_string in search_strings:
                        query = query | SearchQuery(search_string)
                        # fuzzy_search |= Q(content__contains=search_string)

                    annotations = annotations.annotate(
                        search=vector
                    ).filter(
                        search=query
                    )

                    user_annotations = user_annotations.annotate(
                        search=vector
                        ).filter(
                            search=query
                        )

                annotation_results = annotations.values(
                    'canvas__position',
                    'canvas__manifest__pid',
                    'canvas__pid'
                    ).annotate(
                        Count('canvas__position')
                    ).order_by(
                        'canvas__position'
                    ).exclude(
                        resource_type='dctypes:Text'
                    ).distinct()

                for annotation in annotation_results:
                    results['ocr_annotations'].append(json.dumps(annotation))

                user_annotation_results = user_annotations.values(
                    'canvas__position',
                    'canvas__manifest__pid',
                    'canvas__pid'
                ).annotate(
                    rank=SearchRank(vector, query)
                ).order_by(
                    '-rank'
                ).distinct()

                for ua_annotation in user_annotation_results:
                    results['user_annotations'].append(json.dumps(ua_annotation))

        except MultiValueDictKeyError:
            pass

        LOGGER.debug(results)
        return results

    def get(self, request, *args, **kwargs): # pylint: disable = unused-argument
        """
        Respond to GET requests for search queries.

        :rtype: JsonResponse
        """
        return JsonResponse(
            status=200,
            data=self.get_queryresults()
        )
