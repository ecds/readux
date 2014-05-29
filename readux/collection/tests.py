from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from mock import patch, NonCallableMock

from eulfedora.server import Repository
from readux.collection.models import Collection
from readux.books.models import Volume, SolrVolume

class CollectionTest(TestCase):

    def test_short_label(self):
        repo = Repository()
        coll = repo.get_object(type=Collection)
        coll.label = 'Large-Scale Digitization Initiative (LSDI) - Civil War Literature Collection'

        self.assertEqual('Civil War Literature', coll.short_label)


@patch('readux.collection.views.solr_interface')
class CollectionViewsTest(TestCase):

    def test_browse(self, mocksolr_interface):
        mocksolr = mocksolr_interface.return_value

        # simulate sunburnt's fluid interface
        mocksolr.query.return_value = mocksolr.query
        for method in ['query', 'facet_by', 'sort_by', 'field_limit',
                       'exclude', 'filter', 'join', 'paginate']:
            getattr(mocksolr.query, method).return_value = mocksolr.query

        # set up mock results for collection query and facet counts
        solr_result = [
            {'pid': 'coll:1', 'title': 'Yellowbacks'},
            {'pid': 'coll:2', 'title': 'Emory Yearbooks'},
        ]
        mocksolr.query.__iter__.return_value = iter(solr_result)
        mocksolr.query.execute.return_value.facet_counts.facet_fields = {
            'collection_id': [('coll:1', 1), ('coll:2', 5)]
        }

        response = self.client.get(reverse('collection:browse'))

        # inspect solr query args
        # - collection search
        mocksolr.query.filter.assert_called_with(owner='LSDI-project')
        mocksolr.query.assert_any_call(content_model=Collection.COLLECTION_CONTENT_MODEL)
        mocksolr.query.sort_by.assert_called_with('title_exact')
        # - volume facet to get count by collection
        mocksolr.query.assert_any_call(content_model=Volume.VOLUME_CONTENT_MODEL)
        mocksolr.query.facet_by.assert_called_with('collection_id', sort='count', mincount=1)
        mocksolr.query.paginate.assert_called_with(rows=0)

        # inspect titles and counts displayed in response
        self.assertContains(response, solr_result[0]['title'],
            msg_prefix='collection title %(title)s should be displayed' % solr_result[0])
        self.assertContains(response, reverse('collection:view', kwargs={'pid': solr_result[0]['pid']}),
            msg_prefix='page should link to collection view for %(pid)s' % solr_result[0])
        self.assertContains(response, '1 volume',
            msg_prefix='volume count should be displayed')
        self.assertContains(response, solr_result[1]['title'],
            msg_prefix='collection title %(title)s should be displayed' % solr_result[1])
        self.assertContains(response, reverse('collection:view', kwargs={'pid': solr_result[1]['pid']}),
            msg_prefix='page should link to collection view for %(pid)s' % solr_result[1])
        self.assertContains(response, '5 volumes',
            msg_prefix='volume count should be displayed and properly pluralized')


    @patch('readux.collection.views.Repository')
    @patch('readux.collection.views.Paginator', spec=Paginator)
    def test_view(self, mockpaginator, mockrepo, mocksolr_interface):
        mocksolr = mocksolr_interface.return_value
        view_url = reverse('collection:view', kwargs={'pid': 'coll'})

        # simulate 404
        mockcoll = NonCallableMock()
        mockrepo.return_value.get_object.return_value = mockcoll
        # - doesn't exist
        mockcoll.exists = False
        response = self.client.get(view_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected status code %s but got %s for view collection when object doesn\'t exist' % \
            (expected, got))
        # - exists but is the wrong type
        mockcoll.exists = True
        mockcoll.has_requisite_content_models = False
        response = self.client.get(view_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected status code %s but got %s for view collection when object has wrong cmodels' % \
            (expected, got))

        # simulate valid fedora object
        mockcoll.has_requisite_content_models = True
        mockcoll.short_label = 'Yellowbacks'
        mockcoll.pid = 'coll:1'
        # simulate sunburnt's fluid interface
        mocksolr.query.return_value = mocksolr.query
        for method in ['query', 'sort_by', 'results_as']:
            getattr(mocksolr.query, method).return_value = mocksolr.query

        # set up mock results for display on template
        solr_result = [
            SolrVolume(**{'pid': 'vol:1', 'title': 'Asodecoan'}),
            SolrVolume(**{'pid': 'vol:2', 'title': 'Sugar Crop of Lousiana', 'label': 'ocm123_V.2'}),
        ]

        # - using a noncallable for the pagination result that is used in the template
        # because passing callables into django templates does weird things
        mockpage = NonCallableMock()
        mockpaginator.return_value.page.return_value = mockpage
        mockpage.object_list = solr_result
        mockpage.has_other_pages = False
        mockpage.paginator.count = 2
        mockpage.paginator.page_range = [1]

        response = self.client.get(view_url)
        # print response
        # inspect solr query
        mocksolr.query.assert_called_with(content_model=Volume.VOLUME_CONTENT_MODEL,
                                          collection_id=mockcoll.pid)
        mocksolr.query.sort_by.assert_any_call('title_exact')
        mocksolr.query.sort_by.assert_any_call('label')
        mocksolr.query.results_as.assert_called_with(SolrVolume)

        # inspect html result
        self.assertContains(response, mockcoll.short_label,
            msg_prefix='collection short label should be displayed')
        self.assertContains(response,
            '<title>Readux | Collections | %s</title>' % mockcoll.short_label,
            html=True,
            msg_prefix='collection label should be included in html title')
        self.assertContains(response, '2 volumes in this collection',
            msg_prefix='total count of volumes in the collection should be displayed')
        self.assertContains(response, solr_result[0]['title'],
            msg_prefix='volume title %(title)s should be displayed' % solr_result[0])
        self.assertContains(response, solr_result[1]['title'],
            msg_prefix='volume title %(title)s should be displayed' % solr_result[1])
        self.assertContains(response, '(V.2)',
            msg_prefix='volume number should be displayed when present')

        # check that unapi / zotero harvest is enabled
        self.assertContains(response,
            '<link rel="unapi-server" type="application/xml" title="unAPI" href="%s" />' % \
            reverse('books:unapi'),
            html=True,
            msg_prefix='link to unAPI server URL should be specified in header')
        self.assertContains(response,
            '<abbr class="unapi-id" title="%s"></abbr>' % solr_result[0]['pid'],
            msg_prefix='unapi item id for %s should be included to allow zotero harvest' % \
                        solr_result[0]['pid'])
        self.assertContains(response,
            '<abbr class="unapi-id" title="%s"></abbr>' % solr_result[1]['pid'],
            msg_prefix='unapi item id for %s should be included to allow zotero harvest' % \
                       solr_result[1]['pid'])

