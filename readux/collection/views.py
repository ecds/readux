from random import shuffle
from urllib import urlencode

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import Http404
from django.views.decorators.http import last_modified
from django.shortcuts import render
from eulfedora.server import Repository

from readux.utils import solr_interface
from readux.books.models import VolumeV1_0, SolrVolume
from readux.collection import view_helpers
from readux.collection.models import Collection, SolrCollection


def site_index(request):
    # placeholder index page (probably shouldn't be in readux.collection)
    return render(request, 'site_base.html')


@last_modified(view_helpers.collections_modified)
def browse(request, mode='covers'):
    ''''Browse list of all collections sorted by title, with the
    count of volumes in each.

    :param mode: one of covers or list; determines whether collections
        are displayed with covers only, or in list detail view

    '''
    solr = solr_interface()
    # FIXME: this filter should probably be commonly used across all LSDI
    # search and browse
    results = solr.query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
                  .filter(owner='LSDI-project') \
                  .sort_by('title_exact') \
                  .results_as(SolrCollection)
    # NOTE: returning as SolrCollection in order to provide access to
    # associated CollectionImage db model

    # Use a facet query to get a count of the number of volumes in each collection
    q = solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL) \
            .facet_by('collection_id', sort='count', mincount=1) \
            .paginate(rows=0)
    facets = q.execute().facet_counts.facet_fields
    # convert into dictionary for access by pid
    collection_counts = dict([(pid, total) for pid, total in facets['collection_id']])
    # generate a list of tuple of solr result, volume count,
    # filtering out any collections with no items
    collections = [(r, collection_counts.get(r['pid'])) for r in results
                  if r['pid'] in collection_counts]

    # generate a random list of 4 covers for use in twitter gallery card
    # - restrict to collections with cover images
    covers = [coll.cover for coll, count in collections if coll.cover]
    # - randomize the list in place so we can grab the first N
    shuffle(covers)

    return render(request, 'collection/browse.html',
        {'collections': collections, 'mode': mode,
         'meta_covers': covers[:4]})


@last_modified(view_helpers.collection_modified)
def view(request, pid, mode='list'):
    '''View a single collection, with a paginated list of the volumes
    it includes (volumes sorted by title and then ocm number/volume).

    :param mode: one of covers or list; determines whether books in the
        collection are displayed with covers only, or in list detail view
    '''

    repo = Repository(request=request)
    obj = repo.get_object(pid, type=Collection)
    # if pid doesn't exist or isn't a collection, 404
    if not obj.exists or not obj.has_requisite_content_models:
        raise Http404

    # search for all books that are in this collection
    solr = solr_interface()
    q = solr.query(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL,
                   collection_id=obj.pid) \
                .sort_by('title_exact').sort_by('label') \
                .results_as(SolrVolume)
    # sort by title and then by label so multi-volume works should group
    # together in the correct order

    # paginate the solr result set
    paginator = Paginator(q, 30)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        results = paginator.page(page)
    except (EmptyPage, InvalidPage):
        results = paginator.page(paginator.num_pages)

    # url parameters for pagination links
    url_params = request.GET.copy()
    if 'page' in url_params:
        del url_params['page']

    return render(request, 'collection/view.html',
        {'collection': obj, 'items': results, 'mode': mode,
         'url_params': urlencode(url_params),
         'current_url_params': urlencode(request.GET.copy())})
