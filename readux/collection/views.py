from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import Http404
from django.shortcuts import render
from eulfedora.server import Repository
from urllib import urlencode

from readux.utils import solr_interface
from readux.books.models import Volume, SolrVolume
from readux.collection.models import Collection


def site_index(request):
    # placeholder index page (probably shouldn't be in readux.collection)
    return render(request, 'site_base.html')

def browse(request):
    ''''Browse list of all collections sorted by title, with the
    count of volumes in each'''
    solr = solr_interface()
    # FIXME: this filter should probably be commonly used across all LSDI
    # search and browse
    results = solr.query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
                  .filter(owner='LSDI-project') \
                  .sort_by('title_exact')

    # Use a facet query to get a count of the number of volumes in each collection
    q = solr.query(content_model=Volume.VOLUME_CONTENT_MODEL) \
            .facet_by('collection_id', sort='count', mincount=1) \
            .paginate(rows=0)
    facets = q.execute().facet_counts.facet_fields
    # convert into dictionary for access by pid
    collection_counts = dict([(pid, total) for pid, total in facets['collection_id']])
    # generate a list of tuple of solr result, volume count
    collections = [(r, collection_counts.get(r['pid'], 0)) for r in results]

    return render(request, 'collection/browse.html',
        {'collections': collections})


def view(request, pid):
    '''View a single collection, with a paginated list of the volumes
    it includes (volumes sorted by title and then ocm number/volume).'''

    repo = Repository(request=request)
    obj = repo.get_object(pid, type=Collection)
    # if pid doesn't exist or isn't a collection, 404
    if not obj.exists or not obj.has_requisite_content_models:
        raise Http404

    # search for all books that are in this collection
    solr = solr_interface()
    q = solr.query(content_model=Volume.VOLUME_CONTENT_MODEL,
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
        {'collection': obj, 'items': results,
         'url_params': urlencode(url_params)})
