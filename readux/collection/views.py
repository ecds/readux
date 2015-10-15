from random import shuffle
from urllib import urlencode

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView, DetailView


from eulfedora.server import Repository

from readux.utils import solr_interface
from readux.books.models import Volume, SolrVolume
from readux.collection import view_helpers
from readux.collection.models import Collection, SolrCollection
from readux.views import VaryOnCookieMixin

# currently unused
# def site_index(request):
#     # placeholder index page (probably shouldn't be in readux.collection)
#     return render(request, 'site_base.html')


class CollectionList(ListView):
    model = Collection
    template_name = 'collection/collection_list.html'
    display_mode = 'list'

    @method_decorator(last_modified(view_helpers.collections_modified))
    def dispatch(self, *args, **kwargs):
        return super(CollectionList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        solr = solr_interface()
        return solr.query(content_model=Collection.COLLECTION_CONTENT_MODEL) \
                  .filter(owner='LSDI-project') \
                  .sort_by('title_exact') \
                  .results_as(SolrCollection)

    def get_context_data(self, **kwargs):
        solr = solr_interface()
        q = solr.query(content_model=Volume.VOLUME_CMODEL_PATTERN) \
                .facet_by('collection_id', sort='count', mincount=1) \
                .paginate(rows=0)
        facets = q.execute().facet_counts.facet_fields
        # convert into dictionary for access by pid
        collection_counts = dict([(pid, total) for pid, total in facets['collection_id']])
        # generate a list of tuple of solr result, volume count,
        # filtering out any collections with no items
        collections = [(r, collection_counts.get(r['pid'])) for r in self.object_list
                      if r['pid'] in collection_counts]

        # generate a random list of 4 covers for use in twitter gallery card
        # - restrict to collections with cover images
        covers = [coll.cover for coll, count in collections if coll.cover]
        # - randomize the list in place so we can grab the first N
        shuffle(covers)

        return {'collections': collections, 'mode': self.display_mode,
                'meta_covers': covers[:4]}


class CollectionCoverList(CollectionList):
    display_mode = 'covers'


class CollectionDetail(DetailView, VaryOnCookieMixin):
    '''View a single collection, with a paginated list of the volumes
    it includes (volumes sorted by title and then ocm number/volume).
    '''
    model = Collection
    template_name = 'collection/collection_detail.html'
    context_object_name = 'collection'
    display_mode = 'list'

    @method_decorator(last_modified(view_helpers.collection_modified))
    def dispatch(self, *args, **kwargs):
        return super(CollectionDetail, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        # kwargs are set based on configured url pattern
        pid = self.kwargs['pid']
        repo = Repository(request=self.request)
        obj = repo.get_object(pid, type=Collection)
        # if pid doesn't exist or isn't a collection, 404
        if not obj.exists or not obj.has_requisite_content_models:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context_data = super(CollectionDetail, self).get_context_data()
        # sort: currently supports title or date added
        sort = self.request.GET.get('sort', None)

        if self.request.user.is_authenticated():
            notes = Volume.volume_annotation_count(self.request.user)
            domain = get_current_site(self.request).domain
            if not domain.startswith('http'):
                domain = 'http://' + domain
            annotated_volumes = dict([(k.replace(domain, ''), v)
                 for k, v in notes.iteritems()])
        else:
            annotated_volumes = {}

        # search for all books that are in this collection
        solr = solr_interface()
        q = solr.query(content_model=Volume.VOLUME_CMODEL_PATTERN,
                       collection_id=self.object.pid) \
                .results_as(SolrVolume)

        # url parameters for pagination and facet links
        url_params = self.request.GET.copy()

        # generate list for display and removal of active filters
        # NOTE: borrowed from books.view.search
        display_filters = []
        # active filter - only show volumes with pages loaded
        if 'read_online' in self.request.GET and self.request.GET['read_online']:
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
            page = int(self.request.GET.get('page', '1'))
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
        url_params = self.request.GET.copy()
        if 'page' in url_params:
            del url_params['page']
        sort_url_params = self.request.GET.copy()
        if 'sort' in sort_url_params:
            del sort_url_params['sort']

        context_data.update({
             'items': results.object_list,
             'mode': self.display_mode,
             'url_params': urlencode(url_params),
             'sort_url_params': urlencode(sort_url_params),
             'current_url_params': urlencode(self.request.GET.copy()),
             'sort': sort, 'sort_options': sort_options,
             'annotated_volumes': annotated_volumes,
             'facets': facets,  # available facets
             'filters': display_filters,  # active filters
             # for compatibility with class-based view pagination
             'paginator': paginator,
             'page_obj': results,

             })
        return context_data


class CollectionCoverDetail(CollectionDetail):
    display_mode = 'covers'
