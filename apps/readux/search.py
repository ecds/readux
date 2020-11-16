"""Search Endpoint(s)"""
import json
from urllib.parse import urlencode
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView
from django.db.models import Count, Q
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from ..iiif.annotations.models import Annotation
from ..iiif.canvases.models import Canvas
from ..iiif.kollections.models import Collection
from ..iiif.manifests.models import Manifest
from .models import UserAnnotation

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
        annotations = Annotation.objects.filter(
            canvas__manifest__label=manifest.label
        )
        user_annotations = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        ).filter(
            canvas__manifest__label=manifest.label
        )
        user_annotations_index = UserAnnotation.objects.filter(
            owner_id=self.request.user.id
        )
        fuzzy_search = Q()
        query = SearchQuery('')
        vector = SearchVector('content')
        search_type = self.request.GET['type']
        search_strings = self.request.GET['query'].split()
        results = {
            'search_terms': search_strings,
            'ocr_annotations': [],
            'user_annotations': [],
            'user_annotations_index': []
        }

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

            user_annotations_index_results = user_annotations_index.values(
                'canvas__position',
                'canvas__manifest__pid',
                'canvas__pid'
                ).annotate(
                    Count('canvas__position')
                ).order_by(
                    'canvas__position'
                ).distinct()

            for ua_annotation_index in user_annotations_index_results:
                results['user_annotations_index'].append(json.dumps(ua_annotation_index))

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

# class VolumeSearch(ListView):
#     """Search across all volumes."""
#     template_name = 'search_results.html'

#     def get_queryset(self):
#         return Manifest.objects.all()

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         collection = self.request.GET.get('collection', None)
#         # pylint: disable = invalid-name
#         COLSET = Collection.objects.values_list('pid', flat=True)
#         COL_OPTIONS = list(COLSET)
#         COL_LIST = Collection.objects.values('pid', 'label').order_by('label').distinct('label')
#         # pylint: enable = invalid-name
#         collection_url_params = self.request.GET.copy()

#         manifests = self.get_queryset()
#         try:
#             # search_string = self.request.GET['q']
#             search_type = self.request.GET['type']
#             search_strings = self.request.GET['q'].split()
#             query = SearchQuery('')
#             canvas_content_query = Q()

#             weighted_vector = SearchVector(
#                 'label', weight='A'
#                 ) + SearchVector(
#                     'author', weight='B'
#                 ) + SearchVector(
#                     'summary', weight='C'
#                 )

#             vector = SearchVector('canvas__annotation__content')

#             if search_strings:
#                 if search_type == 'partial':
#                     canvas_metadata_query = Q()
#                     for search_string in search_strings:
#                         query = query | SearchQuery(search_string)
#                         canvas_content_query |= Q(
#                             canvas__annotation__content__icontains=search_string
#                         )
#                         canvas_metadata_query |= Q(label__icontains=search_string) | \
#                             Q(author__icontains=search_string) | \
#                             Q(summary__icontains=search_string)

#                     canvas_content_results = manifests.filter(canvas_content_query)

#                     canvas_content_results = canvas_content_results.values(
#                         'pid', 'label', 'author',
#                         'published_date', 'created_at'
#                     ).annotate(
#                         pidcount=Count('pid')
#                     ).order_by('-pidcount')

#                     canvas_metadata_results = manifests.filter(canvas_metadata_query)
#                     manifest_results = manifests.values(
#                         'label', 'author', 'published_date', 'created_at', 'canvas__pid', 'pid',
#                         'canvas__IIIF_IMAGE_SERVER_BASE__IIIF_IMAGE_SERVER_BASE'
#                     ).order_by(
#                         'pid'
#                     ).distinct(
#                         'pid'
#                     )

#                     if collection not in COL_OPTIONS:
#                         collection = None

#                     if collection is not None:
#                         canvas_content_results = canvas_content_results.filter(
#                             collections__pid=collection
#                         )
#                         canvas_metadata_results = canvas_metadata_results.filter(collections__pid=collection)

#                     if 'collection' in collection_url_params:
#                         del collection_url_params['collection']

#                 elif search_type == 'exact':
#                     for search_string in search_strings:
#                         query = query | SearchQuery(search_string)
#                         canvas_content_query |= Q(canvas__annotation__content__exact=search_string)
#                     canvas_content_results = manifests.annotate(
#                         search=vector
#                         ).filter(
#                             search=query
#                         ).annotate(
#                             rank=SearchRank(vector, query)
#                         ).values(
#                             'pid', 'label', 'author',
#                             'published_date', 'created_at'
#                         ).annotate(
#                             pidcount=Count('pid')
#                         ).order_by('-pidcount')

#                     canvas_metadata_results = manifests.annotate(
#                         search=weighted_vector
#                         ).filter(
#                             search=query
#                         ).annotate(
#                             rank=SearchRank(weighted_vector, query)
#                         ).values(
#                             'pid', 'label', 'author',
#                             'published_date', 'created_at'
#                         ).order_by(
#                             '-rank'
#                         )

#                     manifest_results = manifests.values(
#                         'canvas__pid', 'pid',
#                         'canvas__IIIF_IMAGE_SERVER_BASE__IIIF_IMAGE_SERVER_BASE'
#                     ).order_by(
#                         'pid'
#                     ).distinct('pid')

#                     if collection not in COL_OPTIONS:
#                         collection = None

#                     if collection is not None:
#                         canvas_content_results = canvas_content_results.filter(
#                             collections__pid=collection
#                         )
#                         canvas_metadata_results = canvas_metadata_results.filter(
#                             collections__pid=collection
#                         )

#                     if 'collection' in collection_url_params:
#                         del collection_url_params['collection']
#             else:
#                 # search_string = ''
#                 search_strings = ''
#                 canvas_content_results = ''
#                 manifest_results = ''
#                 canvas_metadata_results = ''
#             context['canvas_content_results'] = canvas_content_results
#             context['manifest_results'] = manifest_results
#             context['canvas_metadata_results'] = canvas_metadata_results
#         except MultiValueDictKeyError:
#             q = ''
#             # search_string = ''
#             search_strings = ''

#         context['volumes'] = manifests.all
#         annocount_list = []
#         canvaslist = []
#         for volume in manifests:
#             user_annotation_count = UserAnnotation.objects.filter(
#                 owner_id=self.request.user.id
#             ).filter(
#                 canvas__manifest__id=volume.id
#             ).count()
#             annocount_list.append({volume.pid: user_annotation_count})
#             context['user_annotation_count'] = annocount_list
#             canvasquery = Canvas.objects.filter(is_starting_page=1).filter(manifest__id=volume.id)
#             canvasquery2 = list(canvasquery)
#             canvaslist.append({volume.pid: canvasquery2})
#             context['firstthumbnail'] = canvaslist
#         context.update({
#             'collection_url_params': urlencode(collection_url_params),
#             'collection': collection, 'COL_OPTIONS': COL_OPTIONS,
#             'COL_LIST': COL_LIST, 'search_string': search_string, 'search_strings': search_strings
#         })
#         return context
