from random import shuffle
from urllib import urlencode

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie

from eulfedora.server import Repository

from readux.utils import solr_interface
from readux.books.models import Volume, SolrVolume
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
    results = solr.query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
                  .filter(owner='LSDI-project') \
                  .sort_by('title_exact') \
                  .results_as(SolrCollection)
    # NOTE: returning as SolrCollection in order to provide access to
    # associated CollectionImage db model

    # Use a facet query to get a count of the number of volumes in each collection
    # q = solr.query(solr.Q(content_model=VolumeV1_0.VOLUME_CONTENT_MODEL) | solr.Q(content_model=VolumeV1_1.VOLUME_CONTENT_MODEL)) \

    q = solr.query(content_model=Volume.VOLUME_CMODEL_PATTERN) \
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

@vary_on_cookie
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

    # sort: currently supports title or date added
    sort = request.GET.get('sort', None)

    if request.user.is_authenticated():
        notes = Volume.volume_annotation_count(request.user)
        domain = get_current_site(request).domain
        if not domain.startswith('http'):
            domain = 'http://' + domain
        annotated_volumes = dict([(k.replace(domain, ''), v)
             for k, v in notes.iteritems()])
    else:
        annotated_volumes = {}

    # search for all books that are in this collection
    solr = solr_interface()
    q = solr.query(content_model=Volume.VOLUME_CMODEL_PATTERN,
                   collection_id=obj.pid) \
            .results_as(SolrVolume)

    # url parameters for pagination and facet links
    url_params = request.GET.copy()

    # generate list for display and removal of active filters
    # NOTE: borrowed from books.view.search
    display_filters = []
    # active filter - only show volumes with pages loaded
    if 'read_online' in request.GET and request.GET['read_online']:
        q = q.query(page_count__gt=1)
        unfacet_urlopts = url_params.copy()
        del unfacet_urlopts['read_online']
        display_filters.append(('Read online', '',
                                unfacet_urlopts.urlencode()))
    else:
        # generate a facet count for books with pages loaded
        q = q.facet_query(page_count__gt=1)


    sort_options = ['title', 'date added']
    if sort not in sort_options:
        # by default, sort by title
        sort = 'title'

    if sort == 'title':
        # sort by title and then by label so multi-volume works should group
        # together in the correct order
        q = q.sort_by('title_exact').sort_by('label')
    elif sort == 'date added':
        # sort by most recent creation date (newest additions first)
        q = q.sort_by('-created')

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

    # facets for diplay
    facet_counts = results.object_list.facet_counts
    facets = {}
    if facet_counts.facet_queries:
        # number of volumes with pages loaded;
        # facet query is a list of tuple; second value is the count
        pages_loaded = facet_counts.facet_queries[0][1]
        if pages_loaded < q.count():
            facets['pages_loaded'] = facet_counts.facet_queries[0][1]


    # url parameters for pagination & sort links
    url_params = request.GET.copy()
    if 'page' in url_params:
        del url_params['page']
    sort_url_params = request.GET.copy()
    if 'sort' in sort_url_params:
        del sort_url_params['sort']

    return render(request, 'collection/view.html',
        {'collection': obj, 'items': results, 'mode': mode,
         'url_params': urlencode(url_params),
         'sort_url_params': urlencode(sort_url_params),
         'current_url_params': urlencode(request.GET.copy()),
         'sort': sort, 'sort_options': sort_options,
         'annotated_volumes': annotated_volumes,
         'facets': facets,  # available facets
         'filters': display_filters,  # active filters
         })
