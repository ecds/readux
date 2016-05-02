from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template.defaultfilters import filesizeformat
from django.test import TestCase
import json
from mock import Mock, patch, NonCallableMock, NonCallableMagicMock, \
    MagicMock, call
from urllib import unquote

from readux.annotations.models import Annotation
from readux.books.models import SolrVolume, Volume, Page, SolrPage
from readux.books import sitemaps, views, view_helpers, forms
from readux.utils import absolutize_url


class BookViewsTest(TestCase):
    # borrowing fixture & test accounts from readux.annotations.tests
    fixtures = ['test_annotation_data.json']
    user_credentials = {
        'user': {'username': 'testuser', 'password': 'testing'},
        'superuser': {'username': 'testsuper', 'password': 'superme'}
    }

    # sample datastream profile xml
    xml_profile = '''<datastreamProfile xmlns="http://www.fedora.info/definitions/1/0/management/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.fedora.info/definitions/1/0/management/ http://www.fedora.info/definitions/1/0/datastreamProfile.xsd" pid="synctest:1" dsID="DC">
<dsLabel>Dublin Core Record for this object</dsLabel>
<dsVersionID>DC1.0</dsVersionID>
<dsCreateDate>2016-02-10T16:36:25.913Z</dsCreateDate>
<dsState>A</dsState>
<dsMIME>text/xml</dsMIME>
<dsFormatURI>http://www.openarchives.org/OAI/2.0/oai_dc/</dsFormatURI>
<dsControlGroup>X</dsControlGroup>
<dsSize>379</dsSize>
<dsVersionable>true</dsVersionable>
<dsInfoType/>
<dsLocation>synctest:1+DC+DC1.0</dsLocation>
<dsLocationType/>
<dsChecksumType>MD5</dsChecksumType>
<dsChecksum>cc0db0ef0fcd559065a788a22442d3c7</dsChecksum>
</datastreamProfile>'''

    @patch('readux.books.views.VolumePdf.repository_class')
    @patch('eulfedora.views._raw_datastream')
    def test_pdf(self, mockraw_ds, mockrepo_class):
        mockobj = Mock()
        mockobj.pid = 'vol:1'
        mockobj.label = 'ocm30452349_1908'
        mockrepo = mockrepo_class.return_value
        mockrepo.get_object.return_value = mockobj
        # get datastream called by etag/last-modified methods
        mockrepo.api.getDatastream.return_value.content = self.xml_profile
        mockrepo.api.getDatastream.return_value.url = 'http://fedora.co/objects/ds'

        # to support for last modified conditional
        mockobj.pdf.created = datetime.now()
        # mockrepo.api.getDatastreamDissemination.return_value =
        # mockobj.getDatastreamObject.return_value.created = mockobj.pdf.created

        # class-based view handling requires an actual response
        mockraw_ds.return_value = HttpResponse()

        pdf_url = reverse('books:pdf', kwargs={'pid': mockobj.pid})
        response = self.client.get(pdf_url)

        # only check custom logic implemented here, via mocks
        # (not testing eulfedora.views.raw_datastream logic)
        self.assertEqual(mockraw_ds.return_value, response,
            'result of fedora raw_datastream should be returned')

        # can't check full call args because we can't match request
        args, kwargs = mockraw_ds.call_args

        # second arg should be pid
        self.assertEqual(mockobj.pid, args[1])
        # third arg should be datstream id
        self.assertEqual(Volume.pdf.id, args[2])
        # digital object class should be specified
        self.assertEqual(mockrepo, kwargs['repo'])
        self.assertEqual({'Content-Disposition': 'filename="%s.pdf"' % mockobj.label},
            kwargs['headers'])

        # volume with a space in the label
        mockobj.label = 'ocm30452349_1908 V0.1'
        response = self.client.get(pdf_url)
        args, kwargs = mockraw_ds.call_args
        content_disposition = kwargs['headers']['Content-Disposition']
        self.assertEqual('filename="%s.pdf"' % mockobj.label.replace(' ', '-'),
            content_disposition,
            'content disposition filename should not include spaces even if label does')

        # if object doesn't exist, 404 (don't error on generating headers)
        mockobj.exists = False
        response = self.client.get(pdf_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected %s for %s when there is a fedora error, got %s' % \
            (expected, pdf_url, got))

    @patch('readux.books.views.Paginator', spec=Paginator)
    @patch('readux.books.views.solr_interface')
    @patch('readux.books.views.VolumeSearch.paginate_queryset')
    def test_search(self, mockqs_paginate, mocksolr_interface, mockpaginator):
        mockpage = NonCallableMock()
        search_url = reverse('books:search')

        # NOTE: pagination now happens in django's class-based view,
        # so must be mocked there
        mockqs_paginate.return_value = (mockpaginator.return_value,
            mockpage, [], False)

        # no search terms - invalid form
        response = self.client.get(search_url)
        self.assertContains(response, 'Please enter one or more search terms')

        mocksolr = mocksolr_interface.return_value
        # simulate sunburnt's fluid interface
        mocksolr.query.return_value = mocksolr.query
        for method in ['query', 'facet_by', 'sort_by', 'field_limit',
                       'exclude', 'filter', 'join', 'paginate', 'results_as',
                       'facet_query']:
            getattr(mocksolr.query, method).return_value = mocksolr.query

        # set up mock results for collection query and facet counts
        solr_result = NonCallableMagicMock(spec_set=['__iter__', 'facet_counts'])
        # *only* mock iter, to avoid weirdness with django templates & callables
        solr_result.__iter__.return_value = [
            SolrVolume(**{'pid': 'vol:1', 'title': 'Lecoq, the detective', 'pdf_size': 1024}),
            SolrVolume(**{'pid': 'vol:2', 'title': 'Mabel Meredith', 'pdf_size': 34665}),
        ]
        mocksolr.query.__iter__.return_value = iter(solr_result)
        mocksolr.count.return_value = 2
        # mock facets
        # solr_result.facet_counts.facet_fields = {
        #     'collection_label_facet': [('Civil War Literature', 2), ('Yellowbacks', 4)]
        # }

        # use a noncallable for the pagination result that is used in the template
        # because passing callables into django templates does weird things

        mockpaginator.return_value.page.return_value = mockpage
        results = NonCallableMagicMock(spec=['__iter__', 'facet_counts', '__len__'])

        results.__iter__.return_value = iter(solr_result)
        results.facet_counts.facet_fields = {
            'collection_label_facet': [('Emory Yearbooks', 1), ('Yellowbacks', 4)]
        }
        results.__len__.return_value = 2

        mockpage.object_list = results
        mockpage.has_other_pages = False
        mockpage.paginator.count = 2
        mockpage.paginator.page_range = [1]
        mockpaginator.return_value.count = 2
        mockpaginator.return_value.page_range = [1]
        mockqs_paginate.return_value = (mockpaginator.return_value, mockpage, results, True)

        # query with search terms
        response = self.client.get(search_url, {'keyword': 'yellowbacks'})

        mocksolr.query.filter.assert_called_with(content_model=Volume.VOLUME_CMODEL_PATTERN)
        # because of creator/title search boosting, actual query is a little difficult to test
        mocksolr.Q.assert_any_call('yellowbacks')
        mocksolr.Q.assert_any_call(creator='yellowbacks')
        mocksolr.Q.assert_any_call(title='yellowbacks')
        # not sure how to test query on Q|Q**3|Q**3
        mocksolr.query.field_limit.assert_called_with(SolrVolume.necessary_fields,
            score=True)

        # check that unapi / zotero harvest is enabled
        self.assertContains(response,
            '<link rel="unapi-server" type="application/xml" title="unAPI" href="%s" />' % \
            reverse('books:unapi'),
            html=True,
            msg_prefix='link to unAPI server URL should be specified in header')

        # check that items are displayed
        for item in solr_result:
            self.assertContains(response, item['title'],
                msg_prefix='title should be displayed')
            self.assertContains(response, unquote(reverse('books:pdf', kwargs={'pid': item['pid']})),
                    msg_prefix='link to pdf should be included in response')
            self.assertContains(response,
                '<abbr class="unapi-id" title="%s"></abbr>' % item['pid'],
                msg_prefix='unapi item id for %s should be included to allow zotero harvest' \
                           % item['pid'])
            # pdf size
            self.assertContains(response, filesizeformat(item['pdf_size']),
                msg_prefix='PDF size should be displayed in human-readable format')

        # check that collection facets are displayed / linked
        for coll, count in results.facet_counts.facet_fields['collection_label_facet']:
            self.assertContains(response, coll,
                msg_prefix='collection facet label should be displayed on search results page')
            # not a very definitive test, but at least check the number is displayed
            self.assertContains(response, count,
                msg_prefix='collection facet count should be displayed on search results page')
            self.assertContains(response,
                '?keyword=yellowbacks&amp;collection=%s' % coll.replace(' ', '%20'),
                msg_prefix='response should include link to search filtered by collection facet')

        # multiple terms and phrase
        response = self.client.get(search_url, {'keyword': 'yellowbacks "lecoq the detective" mystery'})
        for term in ['yellowbacks', 'lecoq the detective', 'mystery']:
            mocksolr.Q.assert_any_call(term)

        # filtered by collection
        response = self.client.get(search_url, {'keyword': 'lecoq', 'collection': 'Yellowbacks'})
        mocksolr.query.query.assert_any_call(collection_label='"%s"' % 'Yellowbacks')

        ## annotation totals
        # empty annotation total in context for anonymous user
        self.assertEqual({}, response.context['annotated_volumes'])
        # check that annotation total is retrieved for ONLY logged in users
        with patch('readux.books.views.Volume') as mockvolclass:
            response = self.client.get(search_url, {'keyword': 'lecoq', 'collection': 'Yellowbacks'})
            mockvolclass.volume_annotation_count.assert_not_called()

            User = get_user_model()
            testuser = User.objects.get(username=self.user_credentials['user']['username'])
            self.client.login(**self.user_credentials['user'])
            response = self.client.get(search_url, {'keyword': 'lecoq', 'collection': 'Yellowbacks'})
            mockvolclass.volume_annotation_count.assert_called_with(testuser)

    @patch('readux.books.views.VolumeText.repository_class') #TypeInferringRepository')
    def test_text(self, mockrepo_class):
        mockobj = Mock()
        mockobj.pid = 'vol:1'
        mockobj.label = 'ocm30452349_1908'
        # has to return a datetime (and not a mock) for last-modified conditional
        mockobj.getDatastreamObject.return_value.created = datetime.now()

        mockrepo = mockrepo_class.return_value
        mockrepo.get_object.return_value = mockobj
        # get datastream called by etag/last-modified methods
        mockrepo.api.getDatastream.return_value.content = self.xml_profile
        mockrepo.api.getDatastream.return_value.url = 'http://fedora.co/objects/ds'

        mockobj.get_fulltext.return_value = 'sample text content'
        # to support for last modified conditional
        mockobj.ocr.created = datetime.now()

        text_url = reverse('books:text', kwargs={'pid': mockobj.pid})
        response = self.client.get(text_url)

        self.assertEqual(mockobj.get_fulltext.return_value, response.content,
            'volume full text should be returned as response content')
        self.assertEqual(response['Content-Type'], "text/plain")
        self.assertEqual(response['Content-Disposition'],
            'filename="%s.txt"' % mockobj.label)

        # various 404 conditions
        # - no ocr
        mockobj.fulltext_available = False
        response = self.client.get(text_url)
        self.assertEqual(404, response.status_code,
            'text view should 404 if fultext is not available')
        # - not a volume
        mockobj.has_requisite_content_models = False
        mockobj.ocr.exists = True
        response = self.client.get(text_url)
        self.assertEqual(404, response.status_code,
            'text view should 404 if object is not a Volume')
        # - object doesn't exist
        mockobj.exists = False
        mockobj.has_requisite_content_models = True
        response = self.client.get(text_url)
        self.assertEqual(404, response.status_code,
            'text view should 404 if object does not exist')

    @patch('readux.books.views.Repository')
    def test_unapi(self, mockrepo):
        unapi_url = reverse('books:unapi')

        # no params - should list available formats
        response = self.client.get(unapi_url)
        self.assertEqual('application/xml', response['content-type'],
            'response should be returned as xml')
        self.assertContains(response, '<formats>',
            msg_prefix='request with no parameters should return all formats')
        # volume formats only for now
        formats = Volume.unapi_formats
        for fmt_name, fmt_info in formats.iteritems():
            self.assertContains(response, '<format name="%s" type="%s"' \
                % (fmt_name, fmt_info['type']),
                msg_prefix='formats should include %s' % fmt_name)

        mockobj = Mock()
        mockobj.pid = 'vol:1'
        mockobj.label = 'ocm30452349_1908'
        mockobj.unapi_formats = Volume.unapi_formats
        # actual rdf dc logic tested elsewhere
        mockobj.rdf_dc.return_value = 'sample bogus rdf for testing purposes'
        mockrepo.return_value.get_object.return_value = mockobj

        # request with id but no format
        response = self.client.get(unapi_url, {'id': mockobj.pid})
        self.assertEqual('application/xml', response['content-type'],
            'response should be returned as xml')
        self.assertContains(response, '<formats id="%s">' % mockobj.pid,
            msg_prefix='request with id specified should return formats for that id')
        # volume formats only for now
        for fmt_name, fmt_info in formats.iteritems():
            self.assertContains(response, '<format name="%s" type="%s"' \
                % (fmt_name, fmt_info['type']),
                msg_prefix='formats should include %s' % fmt_name)

        # request with id and format
        response = self.client.get(unapi_url, {'id': mockobj.pid, 'format': 'rdf_dc'})
        self.assertEqual(formats['rdf_dc']['type'], response['content-type'],
            'response content-type should be set based on requested format')
        self.assertEqual(mockobj.rdf_dc.return_value, response.content,
            'response content should be set based on result of method corresponding to requested format')

    @patch('readux.books.views.Repository')
    def test_volume(self, mockrepo):
        mockobj = NonCallableMock()
        mockobj.pid = 'vol:1'
        mockobj.title = 'Lecoq, the detective'
        mockobj.volume = 'V.1'
        mockobj.date = ['1801']
        mockobj.creator = ['Gaboriau, Emile']
        mockobj.book.dc.content.description_list = [
           'Translation of: Monsieur Lecoq.',
           'Victorian yellowbacks + paperbacks, 1849-1905'
        ]
        mockobj.book.dc.content.publisher = 'London : Vizetelly'
        mockobj.book.volume_set = [mockobj, NonCallableMock(pid='vol:2')]
        mockobj.pdf_size = 1024
        mockobj.has_pages = False
        mockobj.is_a_volume = True
        mockrepo.return_value.get_object.return_value = mockobj
        # to support for last modified conditional
        mockobj.ocr.created = datetime.now()

        vol_url = reverse('books:volume', kwargs={'pid': mockobj.pid})
        response = self.client.get(vol_url)
        self.assertContains(response, mockobj.title,
            msg_prefix='response should include title')
        self.assertContains(response, mockobj.volume,
            msg_prefix='response should include volume label')
        self.assertContains(response, mockobj.date[0],
            msg_prefix='response should include date')
        self.assertContains(response, mockobj.creator[0],
            msg_prefix='response should include creator')
        for desc in mockobj.book.dc.content.description_list:
            self.assertContains(response, desc,
                msg_prefix='response should include dc:description')
        self.assertContains(response, mockobj.book.dc.content.publisher,
            msg_prefix='response should include publisher')
        self.assertContains(response, reverse('books:pdf', kwargs={'pid': mockobj.pid}),
            msg_prefix='response should include link to pdf')
        # related volumes
        self.assertContains(response, 'Related volumes',
            msg_prefix='response should include related volumes when present')
        self.assertContains(response,
            reverse('books:volume', kwargs={'pid': mockobj.book.volume_set[0].pid}),
            msg_prefix='response should link to related volumes')
        # pdf size
        self.assertContains(response, filesizeformat(mockobj.pdf_size),
            msg_prefix='PDF size should be displayed in human-readable format')
        # no pages loaded, should not include volume search or read online
        self.assertNotContains(response, 'Read online',
            msg_prefix='volume without pages loaded should not display read online option')
        # NOTE: href needed to differentiate from cover url, which starts the same
        self.assertNotContains(response, 'href="%s"' % reverse('books:pages', kwargs={'pid': mockobj.pid}),
            msg_prefix='volume without pages loaded should not have link to read online')
        self.assertNotContains(response, '<form id="volume-search" ',
            msg_prefix='volume without pages loaded should not have volume search')

        # annotation total passed to context
        self.assert_('annotated_volumes' not in response.context,
            'annotation count should not be set for volumes without pages')

        # simulate volume with pages loaded
        mockobj.has_pages = True
        # to test annotation count
        mockobj.get_absolute_url.return_value = '/books/vol:1/'
        mockobj.annotation_count.return_value = 5

        response = self.client.get(vol_url)
        # *should* include volume search and read online
        self.assertContains(response, 'Read online',
            msg_prefix='volume with pages loaded should display read online option')
        self.assertContains(response, reverse('books:pages', kwargs={'pid': mockobj.pid}),
            msg_prefix='volume with pages loaded should have link to read online')
        self.assertContains(response, '<form id="volume-search" ',
            msg_prefix='volume without pages loaded should have volume search')
        # annotation total passed to context
        self.assertEqual({mockobj.get_absolute_url(): 5},
            response.context['annotated_volumes'],
            'annotation count should be set for volumes with pages')

        mockobj.annotation_count.return_value = 0
        response = self.client.get(vol_url)
        self.assert_('annotated_volumes' not in response.context,
            'annotation count should not be set in context when it is zero')

        # non-existent should 404
        mockobj.exists = False
        response = self.client.get(vol_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected %s for %s when object does not exist, got %s' % \
            (expected, vol_url, got))
        # exists but isn't a volume - should also 404
        mockobj.exists = True
        mockobj.is_a_volume = False
        response = self.client.get(vol_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected %s for %s when object is not a volume, got %s' % \
            (expected, vol_url, got))


    @patch('readux.books.views.Repository')
    @patch('readux.books.views.Paginator', spec=Paginator)
    @patch('readux.books.views.solr_interface')
    def test_volume_page_search(self, mocksolr_interface, mockpaginator, mockrepo):
        mockobj = NonCallableMock()
        mockobj.pid = 'vol:1'
        mockobj.title = 'Lecoq, the detective'
        mockobj.date = ['1801']
        mockrepo.return_value.get_object.return_value = mockobj

        mocksolr = mocksolr_interface.return_value
        # simulate sunburnt's fluid interface
        mocksolr.query.return_value = mocksolr.query
        for method in ['query', 'facet_by', 'sort_by', 'field_limit', 'highlight',
                       'exclude', 'filter', 'join', 'paginate', 'results_as']:
            getattr(mocksolr.query, method).return_value = mocksolr.query

        # set up mock results for collection query and facet counts
        solr_result = NonCallableMagicMock(spec_set=['__iter__', 'facet_counts'])

        # *only* mock iter, to avoid weirdness with django templates & callables
        solr_results = [
            SolrPage(**{'pid': 'page:1', 'page_order': '1', 'score': 0.5,
             'solr_highlights': {'page_text': ['snippet with search term']},
                 'identifier': ['http://testpid.co/ark:/1234/11/']}),
            SolrPage(**{'pid': 'page:233', 'page_order': '123', 'score': 0.02,
             'solr_highlights': {'page_text': ['sample text result from content']},
              'identifier': ['http://testpid.co/ark:/1234/22/']}),
        ]
        solr_result.__iter__.return_value = solr_results
        mocksolr.query.__iter__.return_value = iter(solr_result)
        mocksolr.count.return_value = 2

        mockpage = NonCallableMock()
        mockpaginator.return_value.page.return_value = mockpage
        results = NonCallableMagicMock(spec=['__iter__', 'facet_counts', 'highlighting'])
        results.__iter__.return_value = iter(solr_result)

        mockpage.object_list = results
        mockpage.has_other_pages = False
        mockpage.paginator.count = 2
        mockpage.paginator.page_range = [1]
         # patch in highlighting - apparent change in sunburnt behavior
        results.highlighting = {
            'page:1': {'page_text': ['snippet with search term']},
            'page:233':  {'page_text': ['sample text result from content']}
        }

        vol_url = reverse('books:volume', kwargs={'pid': mockobj.pid})
        response = self.client.get(vol_url, {'keyword': 'determine'})
        self.assertEqual(response.templates[0].name,
            views.VolumeDetail.search_template_name,
            'volume search template should be used for valid search submission')
        for page in iter(solr_result):
            self.assertContains(response,
                reverse('books:page-image', kwargs={'vol_pid': mockobj.pid,
                    'pid': page.pid, 'mode': 'mini-thumbnail'}),
                msg_prefix='search results should include mini page thumbnail url')
            self.assertContains(response, "Page %(page_order)s" % page,
                msg_prefix='search results should include page number')
            self.assertContains(response, page['score'],
                msg_prefix='search results should display page relevance score')
            self.assertContains(response, reverse('books:page',
                kwargs={'vol_pid': mockobj.pid, 'pid': page['pid']}),
                msg_prefix='search results should link to full page view')
            self.assertContains(response, '... %s ...' % page['solr_highlights']['page_text'][0],
                msg_prefix='solr snippets should display when available')

        # ajax request
        with patch('readux.books.views.VolumeDetail.get_context_data') as mock_ctx:
            results = NonCallableMagicMock(spec=['__iter__', 'facet_counts', 'highlighting'])
            results.__iter__.return_value = iter(solr_result)
            results.highlighting = {
                solr_results[0].pid: {
                    'page_text': 'sample highlighting snippet'
                },
                solr_results[1].pid: {
                    'page_text': 'another highlighting snippet'
                }

            }
            mockpage = NonCallableMagicMock(spec=['__iter__'])
            mockpage.object_list = results
            mock_ctx.return_value = {
                 'pages': mockpage,
             }
            response = self.client.get(vol_url, {'keyword': 'determine'},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual('application/json', response['content-type'])
            data = json.loads(response.content)
            for idx in range(len(data)):
                self.assertEqual(solr_results[idx].pid, data[idx]['pid'])
                self.assertEqual('p. %s' % solr_results[idx]['page_order'],
                    data[idx]['label'])
                self.assertEqual(reverse('books:page-image', kwargs={'vol_pid': mockobj.pid,
                    'pid': solr_results[idx].pid, 'mode': 'mini-thumbnail'}),
                    data[idx]['thumbnail'])
                self.assertEqual(results.highlighting[solr_results[idx].pid]['page_text'],
                    data[idx]['highlights'])


    @patch('readux.books.views.Repository')
    @patch('readux.books.views.Paginator', spec=Paginator)
    # @patch('readux.books.views.solr_interface')
    # def test_volume_pages(self, mocksolr_interface, mockpaginator, mockrepo):
    def test_volume_pages(self, mockpaginator, mockrepo):
        mockvol = NonCallableMock(spec=Volume)
        mockvol.pid = 'vol:1'
        mockvol.title = 'Lecoq, the detective'
        mockvol.date = ['1801']
        # second object retrieved from fedora is page, for layout
        mockvol.width = 150
        mockvol.height = 200
        # volume url needed to identify annotations for pages in this volume
        mockvol.get_absolute_url.return_value = reverse('books:volume',
            kwargs={'pid': mockvol.pid})
        mockrepo.return_value.get_object.return_value = mockvol
        mockvol.find_solr_pages = MagicMock()
        mockvol.find_solr_pages.return_value.count = 3
        mockvol.find_solr_pages.__len__.return_value = 3
        mockpage = Mock(width=640, height=400)
        mockvol.pages = [mockpage]

        vol_page_url = reverse('books:pages', kwargs={'pid': mockvol.pid})
        response = self.client.get(vol_page_url)
        # volume method should be used to find pages
        self.assert_(call() in mockvol.find_solr_pages.call_args_list)
        # volume should be set in context
        self.assert_(mockvol, response.context['vol'])
        # annotated pages should be empty for anonymous user
        self.assertEqual({}, response.context['annotated_pages'])

        # log in as a regular user
        self.client.login(**self.user_credentials['user'])
        testuser = get_user_model().objects.get(username=self.user_credentials['user']['username'])

        page1_url = reverse('books:page', kwargs={'vol_pid': mockvol.pid, 'pid': 'page:1'})
        page2_url = reverse('books:page', kwargs={'vol_pid': mockvol.pid, 'pid': 'page:2'})
        page3_url = reverse('books:page', kwargs={'vol_pid': mockvol.pid, 'pid': 'page:3'})
        mockvol.page_annotation_count.return_value = {
          absolutize_url(page1_url): 5,
          absolutize_url(page2_url): 2,
          page3_url: 13
        }
        response = self.client.get(vol_page_url)
        mockvol.page_annotation_count.assert_called_with(testuser)
        annotated_pages = response.context['annotated_pages']
        # counts should be preserved; urls should be non-absolute
        # whether they started that way or not
        self.assertEqual(5, annotated_pages[page1_url])
        self.assertEqual(2, annotated_pages[page2_url])
        self.assertEqual(13, annotated_pages[page3_url])

    @patch('readux.books.views.TypeInferringRepository')
    def test_view_page(self, mockrepo):
        mockobj = Mock()
        mockobj.pid = 'page:1'
        mockobj.volume.pid = 'vol:1'
        mockrepo.return_value.get_object.return_value = mockobj

        url = reverse('books:page',
            kwargs={'vol_pid': mockobj.volume.pid, 'pid': mockobj.pid})

        # doesn't exist
        mockobj.exists = False
        response = self.client.get(url)
        self.assertEqual(404, response.status_code,
            'page view should 404 when object doesn\'t exist')

        # exists but not a page object
        mockobj.exists = True
        response = self.client.get(url)
        self.assertEqual(404, response.status_code,
            'page view should 404 when object isn\'t a Page object')

        # page object
        mockobj = NonCallableMagicMock(spec=Page)
        mockobj.pid = 'page:5'
        mockobj.page_order = 5
        mockobj.display_label = 'Page 5'
        mockobj.volume.pid = 'vol:1'
        # first test without tei
        mockobj.tei = NonCallableMock()  # non-magic mock, to simplify template logic
        mockobj.tei.exists = False
        # uses solr to find adjacent pages
        solr_result = NonCallableMagicMock(spec_set=['__iter__'])
        # *only* mock iter, to avoid weirdness with django templates & callables
        nearby_pages = [
            {'pid': 'page:4', 'page_order': '4'},
            {'pid': 'page:5', 'page_order': '5'},
            {'pid': 'page:5', 'page_order': '6'},
        ]
        solr_result.__iter__.return_value = nearby_pages
        mocksolr_query = MagicMock()
        mocksolr_query.__iter__.return_value = iter(solr_result)
        mocksolr_query.__len__.return_value = 3
        # cheating here, since we know what index should be requested...
        mocksolr_query.__getitem__.return_value = nearby_pages[2]
        mocksolr_query.query.return_value = mocksolr_query
        mockobj.volume.find_solr_pages.return_value = mocksolr_query
        mockrepo.return_value.get_object.return_value = mockobj

        response = self.client.get(url)
        # test expected context variables
        self.assertEqual(mockobj, response.context['page'],
            'page object should be set in context')
        self.assertEqual(nearby_pages[0], response.context['prev'],
            'previous page should be selected from solr result and set in context')
        self.assertEqual(nearby_pages[2], response.context['next'],
            'next page should be selected from solr result and set in context')
        self.assertEqual(1, response.context['page_chunk'],
            'chunk of paginated pages should be calculated and set in context')
        self.assertNotContains(response,
            reverse('books:page-tei',
                kwargs={'vol_pid': mockobj.volume.pid, 'pid': mockobj.pid}),
            msg_prefix='page without tei should NOT link to tei in header')

        # TODO:
        # - test metadata in header (twitter/og fields)
        # - test page image, deep zoom content, title display, etc

        # test with tei available
        mockobj.tei.exists = True
        mockobj.tei.content.page.width = 2000
        mockobj.tei.content.page.height = 1500
        # for now, simulate no ocr content
        mockobj.tei.content.lines = []
        response = self.client.get(url)
        # scale from original page size (long edge) to display size (1000)
        self.assertEqual(0.5, response.context['scale'],
            'page scale should be calculated and set in context')

        # TODO: test tei text content display?

        # FIXME: for some reason, the mocks are not being processed
        # correctly and even though the view can access the volume pid,
        # the template has this:
        # TypeInferringRepository().get_object().volume.__getitem__()'%20id='4568359696'%3E/pages/page:5/tei/" />
        # Test is disabled until this issue can be fixed.
        # self.assertContains(response,
        #     '<link rel="alternate" type="text/xml" href="%s" />' % \
        #         reverse('books:page-tei',
        #             kwargs={'vol_pid': mockobj.volume.pid, 'pid': mockobj.pid}),
        #     html=True,
        #     msg_prefix='page with tei should link to tei in header')

    @patch('readux.books.views.PageTei.repository_class')
    def test_page_tei(self, mockrepo_class):
        mockobj = Mock()
        mockobj.exists = True
        mockobj.pid = 'page:1'
        mockobj.volume.pid = 'vol:1'
        mockds = mockobj.getDatastreamObject.return_value
        mockds.exists = True
        mockds.created = datetime.now()
        mockds.info.size = 100

        mockrepo = mockrepo_class.return_value
        mockrepo = mockrepo_class.return_value
        mockrepo.get_object.return_value = mockobj
        # get datastream called by etag/last-modified methods
        mockrepo.api.getDatastream.return_value.content = self.xml_profile
        mockrepo.api.getDatastream.return_value.url = 'http://fedora.co/objects/ds'
        # required so raw_ds view can update with local headers
        mockrepo.api.getDatastreamDissemination.return_value.headers = {}

        url = reverse('books:page-tei',
            kwargs={'vol_pid': mockobj.volume.pid, 'pid': mockobj.pid})
        response = self.client.get(url)

        # class-based view, can no longer test parameters to raw_datastream
        # only custom logic is the header, and configuration
        self.assertEqual('filename="%s_tei.xml"' % mockobj.pid.replace(':', '-'),
            response['content-disposition'],
            'tei response should have a content-disposition header set')

        mockrepo.api.getDatastreamDissemination.assert_called_with(mockobj.pid,
            Page.tei.id, asOfDateTime=None, rqst_headers={}, stream=True)


    @patch('readux.books.views.TypeInferringRepository')
    def test_page_redirect(self, mockrepo):
        mockobj = Mock()
        mockobj.pid = 'page:1'
        mockobj.volume.pid = 'vol:1'
        mockrepo.return_value.get_object.return_value = mockobj

        url = reverse('books:old-pageurl-redirect',
            kwargs={'pid': mockobj.pid, 'path': ''})

        # doesn't exist
        mockobj.exists = False
        response = self.client.get(url)
        self.assertEqual(404, response.status_code,
            'page redirect view should 404 when object doesn\'t exist')

        # exists but not a page object
        mockobj.exists = True
        response = self.client.get(url)
        self.assertEqual(404, response.status_code,
            'page redirect view should 404 when object isn\'t a Page object')

        # page object
        mockobj = Mock(spec=Page)
        mockobj.pid = 'page:5'
        mockobj.volume.pid = 'vol:1'
        mockobj.exists = True
        mockrepo.return_value.get_object.return_value = mockobj
        response = self.client.get(url, follow=False)
        url_args = {
            'kwargs': {
                'vol_pid': mockobj.volume.pid,
                'pid': mockobj.pid
            }
        }
        self.assertEqual(301, response.status_code,
            'page redirect view should return a permanent redirect')
        self.assertEqual('http://testserver%s' % \
            reverse('books:page', **url_args),
            response['location'])

        # test a couple of sub page urls
        url = reverse('books:old-pageurl-redirect',
            kwargs={'pid': mockobj.pid, 'path': 'tei/'})
        response = self.client.get(url, follow=False)
        self.assertEqual(301, response.status_code,
            'page redirect view should return a permanent redirect')
        self.assertEqual('http://testserver%s' % \
            reverse('books:page-tei', **url_args),
            response['location'])

        url = reverse('books:old-pageurl-redirect',
            kwargs={'pid': mockobj.pid, 'path': 'ocr/'})
        response = self.client.get(url, follow=False)
        self.assertEqual(301, response.status_code,
            'page redirect view should return a permanent redirect')
        self.assertEqual('http://testserver%s' % \
            reverse('books:page-ocr', **url_args),
            response['location'])

    @patch('readux.books.sitemaps.solr_interface')
    def test_sitemaps(self, mocksolr_interface):
        # minimal test, just to check that sitemaps render without error
        response = self.client.get(reverse('sitemap-index'))
        self.assertContains(response, 'sitemapindex')

        response = self.client.get(reverse('sitemap', kwargs={'section': 'volumes'}))
        self.assertContains(response, '<urlset')

    @patch('readux.books.views.Repository')
    def test_volume_export(self, mockrepo):
        mockobj = NonCallableMock()
        mockobj.pid = 'vol:1'
        mockobj.title = 'Lecoq, the detective'
        mockobj.volume = 'V.1'
        mockobj.date = ['1801']
        mockrepo.return_value.get_object.return_value = mockobj
        # to support for last modified conditional
        mockobj.ocr.created = datetime.now()

        # anonymous
        export_url = reverse('books:webexport', kwargs={'pid': mockobj.pid})
        response = self.client.get(export_url)
        self.assertContains(response,
            '''<div class="alert alert-warning">Export functionality is only available
      to logged in users.</div>''',
            msg_prefix='Anonymous user should see warning when viewing export page',
            html=True)
        response = self.client.post(export_url)
        self.assertEqual(400, response.status_code,
            'Anonymous POST to export should return a status of 400 Bad Request')
        self.assertContains(response,
            '''<div class="alert alert-warning">Export functionality is only available
      to logged in users.</div>''',
            msg_prefix='Anonymous user should see warning when viewing export page',
            html=True, status_code=400)

        # log in as a regular user
        self.client.login(**self.user_credentials['user'])
        response = self.client.get(export_url)
        self.assert_('export_form' in response.context,
            'export form should be set in response context for logged in user')
        self.assertContains(response, 'Export to GitHub requires a GitHub account.',
            msg_prefix='user should see a warning about github account')

        # NOTE: currently not testing POST, as it would be difficult
        # and/or not useful to mock


## tests for view helpers

class ViewHelpersTest(TestCase):

    @patch('readux.books.view_helpers.Repository')
    @patch('readux.books.view_helpers.solr_interface')
    def test_volume_pages_modified(self, mocksolr_interface, mockrepo):
        mockvol = Mock(pid='vol:1')
        mockrepo.return_value.get_object.return_value = mockvol

        mockrequest = Mock()
        mockrequest.user.is_authenticated.return_value = False

        # no solr results
        mockresult = MagicMock()
        mocksolr_interface.return_value.query.return_value.sort_by.return_value.field_limit.return_value = mockresult
        mockresult.count.return_value = 0
        lastmod = view_helpers.volume_pages_modified(mockrequest, 'vol:1')
        self.assertEqual(None, lastmod)

        # only solr result
        mockresult.count.return_value = 1
        yesterday = datetime.now() - timedelta(days=1)
        mockresult.__getitem__.return_value = {'timestamp': yesterday}
        lastmod = view_helpers.volume_pages_modified(mockrequest, 'vol:1')
        self.assertEqual(yesterday, lastmod)

        # test with both solr and annotations for logged in user
        mockvol.get_absolute_url.return_value = reverse('books:volume', kwargs={'pid': mockvol.pid})
        mockrequest.user.is_authenticated.return_value = True
        mockrequest.user.username = 'tester'
        testuser = get_user_model()(username='tester')
        testuser.save()
        anno = Annotation.objects.create(user=testuser,
            uri=reverse('books:page', kwargs={'vol_pid': mockvol.pid,
                'pid': 'page:3'}), extra_data=json.dumps({}))
        mockvol.annotations.return_value = Annotation.objects.filter(uri__contains=mockvol.get_absolute_url())
        lastmod = view_helpers.volume_pages_modified(mockrequest, 'vol:1')
        self.assertEqual(anno.created, lastmod)



class SitemapTestCase(TestCase):

    @patch('readux.books.sitemaps.solr_interface')
    def test_volume_sitemap(self, mocksolr_interface):
        vol_sitemap = sitemaps.VolumeSitemap()
        mocksolr = mocksolr_interface.return_value

        # check for expected solr query
        vol_sitemap.items()
        mocksolr.query.assert_called_with(content_model=Volume.VOLUME_CMODEL_PATTERN)
        mocksolr.query.return_value.field_limit.assert_called_with(['pid', 'last_modified'])

    @patch('readux.books.sitemaps.solr_interface')
    def test_volume_page_sitemap(self, mocksolr_interface):
        volpage_sitemap = sitemaps.VolumePageSitemap()
        mocksolr = mocksolr_interface.return_value

        # check for expected solr query
        volpage_sitemap.items()
        mocksolr.query.assert_called_with(content_model=Page.PAGE_CMODEL_PATTERN)
        mocksolr.query.return_value.field_limit.assert_called_with(['pid', 'last_modified',
            'isConstituentOf'])

class BookSearchTest(TestCase):

    def test_search_terms(self):
        form = forms.BookSearch({'keyword': 'term "exact phrase" term2'})
        self.assertTrue(form.is_valid())
        terms = form.search_terms()
        self.assert_('term' in terms)
        self.assert_('term2' in terms)
        self.assert_('exact phrase' in terms)

        # test searching on page ark
        ark = 'http://testpid.library.emory.edu/ark:/25593/pwtbb'
        form = forms.BookSearch({'keyword': ark})
        self.assertTrue(form.is_valid())
        terms = form.search_terms()
        self.assertEqual([ark], terms)



