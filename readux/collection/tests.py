from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch

from eulfedora.server import Repository
from readux.collection.models import Collection
from readux.books.models import Volume

class CollectionTest(TestCase):

    def test_short_label(self):
        repo = Repository()
        coll = repo.get_object(type=Collection)
        coll.label = 'Large-Scale Digitization Initiative (LSDI) - Civil War Literature Collection'

        self.assertEqual('Civil War Literature', coll.short_label)


class CollectionViewsTest(TestCase):

    @patch('readux.collection.views.solr_interface')
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



