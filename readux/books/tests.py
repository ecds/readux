import os
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template.defaultfilters import filesizeformat
from django.test import TestCase
from django.test.utils import override_settings
import json
from mock import patch, Mock, MagicMock, NonCallableMock, \
   NonCallableMagicMock, call
import re
import rdflib
from rdflib import RDF
from urllib import urlencode, unquote

from eulxml.xmlmap import load_xmlobject_from_file, XmlObject,\
    load_xmlobject_from_string
from eulfedora.server import Repository
from eulfedora.util import RequestFailed

from readux.annotations.models import Annotation
from readux.books import abbyyocr
from readux.books.models import SolrVolume, Volume, VolumeV1_0, Book, BIBO, \
    DC, Page, PageV1_0, PageV1_1, TeiFacsimile, TeiZone, SolrPage
from readux.books import sitemaps, view_helpers, views, iiif
from readux.utils import absolutize_url



fixture_dir = os.path.join(settings.BASE_DIR, 'readux', 'books', 'fixtures')


class SolrVolumeTest(TestCase):
    # primarily testing BaseVolume logic here

    def test_properties(self):
        ocm = 'ocn460678076'
        vol = 'V.1'
        noid = '1234'
        volume = SolrVolume(label='%s_%s' % (ocm, vol),
                         pid='testpid:%s' % noid)

        self.assertEqual(ocm, volume.control_key)
        self.assertEqual(vol, volume.volume)
        self.assertEqual(noid, volume.noid)

        # don't display volume zero
        vol = 'V.0'
        volume.data['label'] = '%s_%s' % (ocm, vol)
        self.assertEqual('', volume.volume)

        # should also work without volume info
        volume.data['label'] = ocm
        self.assertEqual(ocm, volume.control_key)
        self.assertEqual('', volume.volume)

    def test_fulltext_absolute_url(self):
        volume = SolrVolume(label='ocn460678076_V.1',
                         pid='testpid:1234')

        url = volume.fulltext_absolute_url()
        self.assert_(url.startswith('http://'))
        self.assert_(url.endswith(reverse('books:text', kwargs={'pid': volume.pid})))
        current_site = Site.objects.get_current()
        self.assert_(current_site.domain in url)

    def test_voyant_url(self):
        # Volume with English Lang
        volume1 = SolrVolume(label='ocn460678076_V.1',
                             pid='testpid:1234', language ='eng')
        url = volume1.voyant_url()

        self.assert_(urlencode({'corpus': volume1.pid}) in url,
            'voyant url should include volume pid as corpus identifier')
        self.assert_(urlencode({'archive': volume1.fulltext_absolute_url()}) in url,
            'voyant url should include volume fulltext url as archive')
        self.assert_(urlencode({'stopList': 'stop.en.taporware.txt'}) in url,
            'voyant url should not include english stopword list when volume is in english')

        # volume language is French
        volume2 = SolrVolume(label='ocn460678076_V.1',
                             pid='testpid:1235', language ='fra')
        url_fra = volume2.voyant_url()
        self.assert_(urlencode({'stopList': 'stop.en.taporware.txt'}) not in url_fra,
            'voyant url should not include english stopword list when language is not english')

    def test_pdf_url(self):
        # no start page set
        vol = SolrVolume(pid='vol:123')
        pdf_url = vol.pdf_url()
        self.assertEqual(unquote(reverse('books:pdf', kwargs={'pid': vol.pid})), pdf_url)
        # start page
        vol = SolrVolume(pid='vol:123', start_page=6)
        pdf_url = vol.pdf_url()
        self.assert_(pdf_url.startswith(unquote(reverse('books:pdf', kwargs={'pid': vol.pid}))))
        self.assert_('#page=6' in pdf_url)

class VolumeTest(TestCase):
    # borrowing fixture & test accounts from readux.annotations.tests
    fixtures = ['test_annotation_data.json']
    user_credentials = {
        'user': {'username': 'testuser', 'password': 'testing'},
        'superuser': {'username': 'testsuper', 'password': 'superme'}
    }

    def test_annotations(self):
        # find annotations associated with a volume, optionally filtered
        # by user

        User = get_user_model()
        testuser = User.objects.create(username='tester')
        testadmin = User.objects.create(username='super', is_superuser=True)

        mockapi = Mock()
        vol = Volume(mockapi, 'vol:1')

        # create annotations to test finding
        p1 = Annotation.objects.create(user=testuser, text='testuser p1',
            uri=reverse('books:page', kwargs={'vol_pid': vol.pid, 'pid': 'p:1'}),
            volume_uri=vol.absolute_url)
        p2 = Annotation.objects.create(user=testuser, text='testuser p2',
            uri=reverse('books:page', kwargs={'vol_pid': vol.pid, 'pid': 'p:2'}),
            volume_uri=vol.absolute_url)
        p3 = Annotation.objects.create(user=testuser, text='testuser p3',
            uri=reverse('books:page', kwargs={'vol_pid': vol.pid, 'pid': 'p:3'}),
            volume_uri=vol.absolute_url)
        v2p1 = Annotation.objects.create(user=testuser, text='testuser vol2 p1',
            uri=reverse('books:page', kwargs={'vol_pid': 'vol:2', 'pid': 'p:1'}),
            volume_uri='http://example.com/books/vol:2/')
        sup2 = Annotation.objects.create(user=testadmin, text='testsuper p2',
            uri=reverse('books:page', kwargs={'vol_pid': vol.pid, 'pid': 'p:2'}),
            volume_uri=vol.absolute_url)
        annotations = vol.annotations()
        self.assertEqual(4, annotations.count())
        self.assert_(v2p1 not in annotations)

        # filter by user
        annotations = vol.annotations(testuser)
        self.assertEqual(3, annotations.count())
        self.assert_(sup2 not in annotations)

        annotations = vol.annotations(testadmin)
        self.assertEqual(4, annotations.count())
        self.assert_(sup2 in annotations)

        # annotation counts per page
        annotation_count = vol.page_annotation_count()
        self.assertEqual(1, annotation_count[p1.uri])
        self.assertEqual(2, annotation_count[p2.uri])
        self.assertEqual(1, annotation_count[p3.uri])
        # by user
        annotation_count = vol.page_annotation_count(testuser)
        self.assertEqual(1, annotation_count[p2.uri])
        annotation_count = vol.page_annotation_count(testadmin)
        self.assertEqual(2, annotation_count[p2.uri])

        # total for a volume
        self.assertEqual(4, vol.annotation_count())
        self.assertEqual(3, vol.annotation_count(testuser))
        self.assertEqual(4, vol.annotation_count(testadmin))

        # total for all volumes
        totals = Volume.volume_annotation_count()
        self.assertEqual(1, totals['http://example.com/books/vol:2/'])
        self.assertEqual(4, totals[vol.absolute_url])
        totals = Volume.volume_annotation_count(testuser)
        self.assertEqual(3, totals[vol.absolute_url])

    def test_has_pages(self):
        mockapi = Mock()
        vol = Volume(mockapi, 'vol:1')
        vol.pages = []
        self.assertFalse(vol.has_pages)
        # one page (i.e. cover image) is not enough to count as having pages
        vol.pages = [Mock(spec=Page)]
        self.assertFalse(vol.has_pages)
        vol.pages = [Mock(spec=Page), Mock(spec=Page)]
        self.assertTrue(vol.has_pages)

    def test_has_tei(self):
        mockapi = Mock()
        vol = Volume(mockapi, 'vol:1')
        p1 = Mock(spec=Page)
        p1.tei.exists = False
        p2 = Mock(spec=Page)
        p2.tei.exists = False
        vol.pages = [p1, p2]
        self.assertFalse(vol.has_tei)
        p2.tei.exists = True
        self.assertTrue(vol.has_tei)



class VolumeV1_0Test(TestCase):

    def setUp(self):
        # use uningested objects for testing purposes
        repo = Repository()
        self.vol = repo.get_object(type=VolumeV1_0)
        self.vol.label = 'ocn460678076_V.1'

    def test_ark_uri(self):
        ark_uri = 'http://pid.co/ark:/12345/ba45'
        self.vol.dc.content.identifier_list.extend([ark_uri, 'pid:ba45', 'otherid'])
        self.assertEqual(ark_uri, self.vol.ark_uri)

    def test_rdf_dc(self):
        # add metadata to test rdf generated
        ark_uri = 'http://pid.co/ark:/12345/ba45'
        self.vol.dc.content.identifier_list.append(ark_uri)
        self.vol.dc.content.title = 'Sunset, a novel'
        self.vol.dc.content.format = 'application/pdf'
        self.vol.dc.content.language = 'eng'
        self.vol.dc.content.rights = 'public domain'

        # NOTE: patching on class instead of instance because related object is a descriptor
        with patch.object(Volume, 'book', new=Mock(spec=Book)) as mockbook:

            mockbook.dc.content.creator_list = ['Author, Joe']
            mockbook.dc.content.date_list = ['1801', '2010']
            mockbook.dc.content.description_list = ['digitized edition', 'mystery novel']
            mockbook.dc.content.publisher = 'Nashville, Tenn. : Barbee &amp; Smith'
            mockbook.dc.content.relation_list = [
                'http://pid.co/ark:/12345/book',
                'http://pid.co/ark:/12345/volpdf'
            ]

            graph = self.vol.rdf_dc_graph()

            lit = rdflib.Literal

            uri = rdflib.URIRef(self.vol.ark_uri)
            self.assert_((uri, RDF.type, BIBO.book) in graph,
                'rdf graph type should be bibo:book')
            self.assert_((uri, DC.title, lit(self.vol.dc.content.title)) in graph,
                'title should be set as dc:title')
            self.assert_((uri, BIBO.volume, lit(self.vol.volume)) in graph,
                'volume label should be set as bibo:volume')
            self.assert_((uri, DC['format'], lit(self.vol.dc.content.format)) in graph,
                'format should be set as dc:format')
            self.assert_((uri, DC.language, lit(self.vol.dc.content.language)) in graph,
                'language should be set as dc:language')
            self.assert_((uri, DC.rights, lit(self.vol.dc.content.rights)) in graph,
                'rights should be set as dc:rights')
            for rel in self.vol.dc.content.relation_list:
                self.assert_((uri, DC.relation, lit(rel)) in graph,
                    'related item %s should be set as dc:relation' % rel)

            # metadata pulled from book obj because not present in volume
            self.assert_((uri, DC.creator, lit(mockbook.dc.content.creator_list[0])) in graph,
                'creator from book metadata should be set as dc:creator when not present in volume metadata')
            self.assert_((uri, DC.publisher, lit(mockbook.dc.content.publisher)) in graph,
                'publisher from book metadata should be set as dc:publisher when not present in volume metadata')
            # earliest date only
            self.assert_((uri, DC.date, lit('1801')) in graph,
                'earliest date 1801 from book metadata should be set as dc:date when not present in volume metadata')

            for d in mockbook.dc.content.description_list:
                self.assert_((uri, DC.description, lit(d)) in graph,
                    'description from book metadata should be set as dc:description when not present in volume metadata')

            # volume-level metadata should be used when present instead of book
            self.vol.dc.content.creator_list = ['Writer, Jane']
            self.vol.dc.content.date_list = ['1832', '2012']
            self.vol.dc.content.description_list = ['digital edition']
            self.vol.dc.content.publisher = 'So &amp; So Publishers'

            graph = self.vol.rdf_dc_graph()

        self.assert_((uri, DC.creator, lit(self.vol.dc.content.creator_list[0])) in graph,
            'creator from volume metadata should be set as dc:creator when present')
        self.assert_((uri, DC.publisher, lit(self.vol.dc.content.publisher)) in graph,
            'publisher from volume metadata should be set as dc:publisher when present')

        # earliest date *only* should be present
        self.assert_((uri, DC.date, lit('1832')) in graph,
            'earliest date 1832 from volume metadata should be set as dc:date when present')

        for d in self.vol.dc.content.description_list:
            self.assert_((uri, DC.description, lit(d)) in graph,
                'description from volume metadata should be set as dc:description when present')

    def test_index_data(self):
        self.vol.owner = ''
        self.vol.dc.content.date = 1842

        # NOTE: patching on class instead of instance because related object is a descriptor
        with patch.object(Volume, 'book', new=Mock(spec=Book)) as mockbook:
            mockbook.pid = 'book:123'
            mockbook.collection.pid = 'coll:123',
            mockbook.collection.short_label = 'Pile O\' Books'
            mockbook.dc.content.creator_list = ['Author, Joe']
            mockbook.dc.content.date_list = ['1801', '2010']
            mockbook.dc.content.description_list = ['digitized edition', 'mystery novel']
            mockbook.dc.content.publisher = 'Nashville, Tenn. : Barbee &amp; Smith'
            mockbook.dc.content.relation_list = [
                'http://pid.co/ark:/12345/book',
                'http://pid.co/ark:/12345/volpdf'
            ]
            mockbook.dc.content.subject_list = []

            data = self.vol.index_data()

            self.assert_('fulltext' not in data,
                'fulltext should not be set in index data when volume has no ocr')
            self.assert_('hasPrimaryImage' not in data,
                'hasPrimaryImage should not be set in index data when volume has no cover')
            self.assertEqual(mockbook.pid, data['book_id'],
                'associated book pid should be set as book id')
            self.assertEqual(mockbook.collection.pid, data['collection_id'],
                'associated collection pid should be set as collection id')
            self.assertEqual(mockbook.collection.short_label, data['collection_label'],
                'associated collection label short label should be set as collection label')
            self.assertEqual(mockbook.dc.content.creator_list, data['creator'],
                'creator should be set from book DC creator')
            self.assertEqual(self.vol.dc.content.date_list, data['date'],
                'date should be set from earliest volume DC date')
            self.assert_('subject' not in data,
                'subject should not be set in index data when book has no subjects')
            self.assertEqual(0, data['page_count'],
                'page count should be set to zero when volume has no pages loaded')

            # test hasPrimaryImage
            mockpage = Mock(spec=Page)
            mockpage.pid = 'page:1234'
            mockpage.uriref = rdflib.URIRef('info:fedora/%s' % mockpage.pid)
            self.vol.primary_image = mockpage
            data = self.vol.index_data()
            self.assertEqual(mockpage.pid, data['hasPrimaryImage'],
                'hasPrimaryImage should be set to cover page pid, when present')

            # test subjects
            mockbook.dc.content.subject_list = ['subj1', 'subj2']
            data = self.vol.index_data()
            self.assertEqual(mockbook.dc.content.subject_list, data['subject'],
                'subject should be set when present in book DC')

            # test full-text
            with patch.object(self.vol, 'ocr') as mockocr:
                mockocr.exists = True
                ocr_xml = load_xmlobject_from_file(os.path.join(fixture_dir,
                    'abbyyocr_fr8v2.xml'))
                mockocr.content = ocr_xml
                data = self.vol.index_data()
                self.assert_('fulltext' in data,
                    'fulltext should be set in index data when OCR is available')

            # use mock to test pdf size indexing
            with patch.object(self.vol, 'pdf') as mockpdf:
                mockpdf.size = 1234567
                data = self.vol.index_data()
                self.assertEqual(mockpdf.size, data['pdf_size'],
                    'pdf_size should be set from pdf size, when available')

    def test_voyant_url(self):
        # NOTE: this test is semi-redundant with the same test for the SolrVolume,
        # but since the method is implemented in BaseVolume and depends on
        # properties set on the subclasses, testing here to ensure it works
        # in both cases

        # no language
        self.vol.pid = 'vol:1234'
        url = self.vol.voyant_url()
        self.assert_(urlencode({'corpus': self.vol.pid}) in url,
            'voyant url should include volume pid as corpus identifier')
        self.assert_(urlencode({'archive': self.vol.fulltext_absolute_url()}) in url,
            'voyant url should include volume fulltext url as archive')
        self.assert_(urlencode({'stopList': 'stop.en.taporware.txt'}) not in url,
            'voyant url should not include english stopword list when volume is not in english')
        # english
        self.vol.dc.content.language = 'eng'
        url = self.vol.voyant_url()
        self.assert_(urlencode({'stopList': 'stop.en.taporware.txt'}) in url,
            'voyant url should include english stopword list when volume is in english')

    def test_get_fulltext(self):
        with patch.object(self.vol, 'ocr') as mockocr:
            mockocr.exists = True
            # abbyy finereader v8
            ocr_xml = load_xmlobject_from_file(os.path.join(fixture_dir,
                'abbyyocr_fr8v2.xml'))
            mockocr.content = ocr_xml

            text = self.vol.get_fulltext()
            # check for arbitrary text content
            self.assert_('In presenting this,  the initial volume of  the' in text,
                'ocr text content should be present in plain text')
            self.assert_('Now, kind reader, we ask that you do not crit' in text,
                'ocr text content should be present in plain text')
            self.assert_(re.search(r'Baldwin\s+Dellinger\s+Brice', text),
                'table row content should be displayed on a single line')

            # abbyy finereader v6
            ocr_xml = load_xmlobject_from_file(os.path.join(fixture_dir,
                'abbyyocr_fr6v1.xml'))
            mockocr.content = ocr_xml

            text = self.vol.get_fulltext()
            # check for arbitrary text content
            self.assert_('was late in the autumn, the vines yet kept their leaves,' in text,
                'ocr text content should be present in plain text')
            self.assert_('walked up the steps. The lady had not moved, and made' in text,
                'ocr text content should be present in plain text')
            self.assert_(re.search(r'Modern\.\s+New Standard\.\s+Popular\.', text),
                'table row content should be displayed on a single line')

    def test_ocr_ids(self):
        # pach in fixture ocr content
        with patch.object(self.vol, 'ocr') as mockocr:
            mockocr.exists = True
            ocr_xml = load_xmlobject_from_file(os.path.join(fixture_dir,
                'abbyyocr_fr8v2.xml'))
            mockocr.content = ocr_xml

            self.assertFalse(self.vol.ocr_has_ids)
            self.vol.add_ocr_ids()
            self.assertTrue(self.vol.ocr_has_ids)

class PageV1_1Test(TestCase):
    metsalto_doc = os.path.join(fixture_dir, 'mets_alto.xml')

    def setUp(self):
        self.mets_alto = load_xmlobject_from_file(self.metsalto_doc, XmlObject)

    def test_ocr_ids(self):
        page = PageV1_1(Mock()) # use mock for fedora api, since we won't make any calls

        with patch.object(page, 'ocr') as mockocr:
            mockocr.exists = True
            mockocr.content = self.mets_alto
            self.assertFalse(page.ocr_has_ids)
            page.add_ocr_ids()
            self.assertTrue(page.ocr_has_ids)

class BookViewsTest(TestCase):
    # borrowing fixture & test accounts from readux.annotations.tests
    fixtures = ['test_annotation_data.json']
    user_credentials = {
        'user': {'username': 'testuser', 'password': 'testing'},
        'superuser': {'username': 'testsuper', 'password': 'superme'}
    }

    @patch('readux.books.views.VolumePdf.repository_class')
    @patch('eulfedora.views.raw_datastream')
    def test_pdf(self, mockraw_ds, mockrepo):
        mockobj = Mock()
        mockobj.pid = 'vol:1'
        mockobj.label = 'ocm30452349_1908'
        mockrepo.return_value.get_object.return_value = mockobj
        # to support for last modified conditional
        mockobj.pdf.created = datetime.now()
        mockobj.getDatastreamObject.return_value.created = mockobj.pdf.created

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
        self.assertEqual(Volume, kwargs['type'])
        self.assertEqual(mockrepo.return_value, kwargs['repo'])
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
    def test_text(self, mockrepo):
        mockobj = Mock()
        mockobj.pid = 'vol:1'
        mockobj.label = 'ocm30452349_1908'
        # has to return a datetime (and not a mock) for last-modified conditional
        mockobj.getDatastreamObject.return_value.created = datetime.now()

        mockrepo.return_value.get_object.return_value = mockobj
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
        solr_result.__iter__.return_value = [
            SolrPage(**{'pid': 'page:1', 'page_order': '1', 'score': 0.5,
             'solr_highlights': {'page_text': ['snippet with search term']}}),
            SolrPage(**{'pid': 'page:233', 'page_order': '123', 'score': 0.02,
             'solr_highlights': {'page_text': ['sample text result from content']}}),
        ]
        mocksolr.query.__iter__.return_value = iter(solr_result)
        mocksolr.count.return_value = 2

        mockpage = NonCallableMock()
        mockpaginator.return_value.page.return_value = mockpage
        results = NonCallableMagicMock(spec=['__iter__', 'facet_counts'])
        results.__iter__.return_value = iter(solr_result)

        mockpage.object_list = results
        mockpage.has_other_pages = False
        mockpage.paginator.count = 2
        mockpage.paginator.page_range = [1]

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
    def test_page_tei(self, mockrepo):
        mockobj = Mock()
        mockobj.exists = True
        mockobj.pid = 'page:1'
        mockobj.volume.pid = 'vol:1'
        mockds = mockobj.getDatastreamObject.return_value
        mockds.exists = True
        mockds.created = datetime.now()
        mockds.info.size = 100
        mockrepo.return_value.get_object.return_value = mockobj

        url = reverse('books:page-tei',
            kwargs={'vol_pid': mockobj.volume.pid, 'pid': mockobj.pid})
        response = self.client.get(url)

        # class-based view, can no longer test parameters to raw_datastream
        # only custom logic is the header, and configuration
        self.assertEqual('filename="%s_tei.xml"' % mockobj.pid.replace(':', '-'),
            response['content-disposition'],
            'tei response should have a content-disposition header set')

        mockobj.getDatastreamObject.assert_called_with(Page.tei.id, as_of_date=None)


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

class SitemapTestCase(TestCase):

    @patch('readux.books.sitemaps.solr_interface')
    def test_volume_sitemap(self, mocksolr_interface):
        vol_sitemap = sitemaps.VolumeSitemap()
        mocksolr = mocksolr_interface.return_value

        # check for expected solr query
        vol_sitemap.items()
        mocksolr.query.assert_called_with(content_model=Volume.VOLUME_CMODEL_PATTERN)
        mocksolr.query.return_value.field_limit.assert_called_with(['pid', 'last_modified'])


class AbbyyOCRTestCase(TestCase):

    fr6v1_doc = os.path.join(fixture_dir, 'abbyyocr_fr6v1.xml')
    fr8v2_doc = os.path.join(fixture_dir, 'abbyyocr_fr8v2.xml')
    # language code
    eng = 'EnglishUnitedStates'

    def setUp(self):
        self.fr6v1 = load_xmlobject_from_file(self.fr6v1_doc, abbyyocr.Document)
        self.fr8v2 = load_xmlobject_from_file(self.fr8v2_doc, abbyyocr.Document)

    def test_document(self):
        # top-level document properties

        # finereader 6 v1
        self.assertEqual(132, self.fr6v1.page_count)
        self.assertEqual(self.eng, self.fr6v1.language)
        self.assertEqual(self.eng, self.fr6v1.languages)
        self.assert_(self.fr6v1.pages, 'page list should be non-empty')
        self.assertEqual(132, len(self.fr6v1.pages),
                         'number of pages should match page count')
        self.assert_(isinstance(self.fr6v1.pages[0], abbyyocr.Page))

        # finereader 8 v2
        self.assertEqual(186, self.fr8v2.page_count)
        self.assertEqual(self.eng, self.fr8v2.language)
        self.assertEqual(self.eng, self.fr8v2.languages)
        self.assert_(self.fr8v2.pages, 'page list should be non-empty')
        self.assertEqual(186, len(self.fr8v2.pages),
                         'number of pages should match page count')
        self.assert_(isinstance(self.fr8v2.pages[0], abbyyocr.Page))

    def test_page(self):
        # finereader 6 v1
        self.assertEqual(1500, self.fr6v1.pages[0].width)
        self.assertEqual(2174, self.fr6v1.pages[0].height)
        self.assertEqual(300, self.fr6v1.pages[0].resolution)
        # second page has picture block, no text
        self.assertEqual(1, len(self.fr6v1.pages[1].blocks))
        self.assertEqual(1, len(self.fr6v1.pages[1].picture_blocks))
        self.assertEqual(0, len(self.fr6v1.pages[1].text_blocks))
        self.assert_(isinstance(self.fr6v1.pages[1].blocks[0], abbyyocr.Block))
        # fourth page has paragraph text
        self.assert_(self.fr6v1.pages[3].paragraphs)
        self.assert_(isinstance(self.fr6v1.pages[3].paragraphs[0],
                                abbyyocr.Paragraph))

        # finereader 8 v2
        self.assertEqual(2182, self.fr8v2.pages[0].width)
        self.assertEqual(3093, self.fr8v2.pages[0].height)
        self.assertEqual(300, self.fr8v2.pages[0].resolution)
        # first page has multiple text/pic blocks
        self.assert_(self.fr8v2.pages[0].blocks)
        self.assert_(self.fr8v2.pages[0].picture_blocks)
        self.assert_(self.fr8v2.pages[0].text_blocks)
        self.assert_(isinstance(self.fr8v2.pages[0].blocks[0], abbyyocr.Block))
        # first page has paragraph text
        self.assert_(self.fr8v2.pages[0].paragraphs)
        self.assert_(isinstance(self.fr8v2.pages[0].paragraphs[0],
                                abbyyocr.Paragraph))

    def test_block(self):
        # finereader 6 v1
        # - basic block attributes
        b = self.fr6v1.pages[1].blocks[0]
        self.assertEqual('Picture', b.type)
        self.assertEqual(144, b.left)
        self.assertEqual(62, b.top)
        self.assertEqual(1358, b.right)
        self.assertEqual(2114, b.bottom)
        # - block with text
        b = self.fr6v1.pages[3].blocks[0]
        self.assert_(b.paragraphs)
        self.assert_(isinstance(b.paragraphs[0], abbyyocr.Paragraph))

        # finereader 8 v2
        b = self.fr8v2.pages[0].blocks[0]
        self.assertEqual('Text', b.type)
        self.assertEqual(282, b.left)
        self.assertEqual(156, b.top)
        self.assertEqual(384, b.right)
        self.assertEqual(228, b.bottom)
        self.assert_(b.paragraphs)
        self.assert_(isinstance(b.paragraphs[0], abbyyocr.Paragraph))

    def test_paragraph_line(self):
        # finereader 6 v1
        para = self.fr6v1.pages[3].paragraphs[0]
        # untested: align, left/right/start indent
        self.assert_(para.lines)
        self.assert_(isinstance(para.lines[0], abbyyocr.Line))
        line = para.lines[0]
        self.assertEqual(283, line.baseline)
        self.assertEqual(262, line.left)
        self.assertEqual(220, line.top)
        self.assertEqual(1220, line.right)
        self.assertEqual(294, line.bottom)
        # line text available via unicode
        self.assertEqual(u'MABEL MEREDITH;', unicode(line))
        # also mapped as formatted text (could repeat/segment)
        self.assert_(line.formatted_text) # should be non-empty
        self.assert_(isinstance(line.formatted_text[0], abbyyocr.Formatting))
        self.assertEqual(self.eng, line.formatted_text[0].language)
        self.assertEqual(u'MABEL  MEREDITH;', line.formatted_text[0].text) # not normalized

        # finereader 8 v2
        para = self.fr8v2.pages[1].paragraphs[0]
        self.assert_(para.lines)
        self.assert_(isinstance(para.lines[0], abbyyocr.Line))
        line = para.lines[0]
        self.assertEqual(1211, line.baseline)
        self.assertEqual(845, line.left)
        self.assertEqual(1160, line.top)
        self.assertEqual(1382, line.right)
        self.assertEqual(1213, line.bottom)
        self.assertEqual(u'EMORY UNIVERSITY', unicode(line))
        self.assert_(line.formatted_text) # should be non-empty
        self.assert_(isinstance(line.formatted_text[0], abbyyocr.Formatting))
        self.assertEqual(self.eng, line.formatted_text[0].language)
        self.assertEqual(u'EMORY UNIVERSITY', line.formatted_text[0].text)

    def test_frns(self):
        self.assertEqual('fr6v1:par|fr8v2:par', abbyyocr.frns('par'))
        self.assertEqual('fr6v1:text/fr6v1:par|fr8v2:text/fr8v2:par',
                         abbyyocr.frns('text/par'))


class TeiFacsimileTest(TestCase):

    def setUp(self):
        # tei generated from mets alto
        self.alto_tei = load_xmlobject_from_file(os.path.join(fixture_dir, 'teifacsimile.xml'),
            TeiFacsimile)
        # tei generated from abbyy ocr
        self.abbyy_tei = load_xmlobject_from_file(os.path.join(fixture_dir, 'teifacsimile_abbyy.xml'),
            TeiFacsimile)

    def test_basic_properties_alto(self):
        self.assert_(isinstance(self.alto_tei.page, TeiZone))
        # quick check page size params coming through
        self.assertEqual(0, self.alto_tei.page.ulx)
        self.assertEqual(0, self.alto_tei.page.uly)
        self.assertEqual(11874, self.alto_tei.page.lrx)
        self.assertEqual(9483, self.alto_tei.page.lry)
        # no easy way to check type (nodelist), so just check that it is non-false
        self.assert_(self.alto_tei.lines,
            'tei facsimile should have a list of lines')
        self.assert_(self.alto_tei.word_zones,
            'tei facsimile should have a list of word zones')
        self.assert_(isinstance(self.alto_tei.word_zones[0], TeiZone))

    def test_basic_properties_abbyy(self):
        self.assert_(isinstance(self.abbyy_tei.page, TeiZone))
        # quick check page size params coming through
        self.assertEqual(0, self.abbyy_tei.page.ulx)
        self.assertEqual(0, self.abbyy_tei.page.uly)
        self.assertEqual(2182, self.abbyy_tei.page.lrx)
        self.assertEqual(3093, self.abbyy_tei.page.lry)
        # no easy way to check type (nodelist), so just check that it is non-false
        self.assert_(self.abbyy_tei.lines,
            'tei facsimile should have a list of lines')
        self.assert_(isinstance(self.abbyy_tei.lines[0], TeiZone))
        # check line content
        self.assertEqual('Presentation', self.abbyy_tei.lines[0].text)

@override_settings(TEI_DISTRIBUTOR='Readux Test Publications')
class OCRtoTEIFacsimileXSLTest(TestCase):

    fr6v1_doc = os.path.join(fixture_dir, 'abbyyocr_fr6v1.xml')
    fr8v2_doc = os.path.join(fixture_dir, 'abbyyocr_fr8v2.xml')
    metsalto_doc = os.path.join(fixture_dir, 'mets_alto.xml')

    def setUp(self):
        self.fr6v1 = load_xmlobject_from_file(self.fr6v1_doc, abbyyocr.Document)
        self.fr8v2 = load_xmlobject_from_file(self.fr8v2_doc, abbyyocr.Document)
        self.mets_alto = load_xmlobject_from_file(self.metsalto_doc, XmlObject)


    def test_pageV1_0(self):
        # page 1.0 - abbyy ocr content

        page = PageV1_0(Mock()) # use mock for fedora api, since we won't make any calls
        page.page_order = 5
        vol = VolumeV1_0(Mock())
        with patch('readux.books.models.PageV1_0.volume') as mockvolume:
            mockvolume.uriref = rdflib.URIRef('vol:1')
            mockvolume.display_label = 'Mabel Meredith'
            mockvolume.volume = None
            mockvolume.creator = ['Townley, Arthur']
            mockvolume.date = '1863'

            # update fixture xml with ids
            with open(VolumeV1_0.ocr_add_ids_xsl) as xslfile:
                result =  self.fr6v1.xsl_transform(filename=xslfile,
                    return_type=unicode)
                fr6v1_with_ids = load_xmlobject_from_string(result,
                    abbyyocr.Document)

            # use the first page with substantial text content as input
            ocr_page = fr6v1_with_ids.pages[5]
            tei = page.generate_tei(ocr_page)
            # NOTE: uncomment to see generated TEI
            # print tei.serialize()

            # should be generating valid tei
            # if not tei.schema_valid():
                # print tei.schema_validation_errors()
            self.assertTrue(tei.schema_valid(),
                'generated TEI facsimile should be schema-valid')
            # inspect the tei and check for expected values
            # - page identifier based on page_order value passed in
            self.assertEqual(ocr_page.id, tei.page.id,
                'tei id should be carried through from ocr xml')
            self.assertEqual(page.display_label, tei.title,
                'tei title should be set from page diplay label')
            # distributor not mapped in teimap, so just use xpath to check
            self.assertEqual(settings.TEI_DISTRIBUTOR,
                tei.node.xpath('string(//t:publicationStmt/t:distributor)',
                    namespaces={'t': tei.ROOT_NS}),
                'configured tei distributor should be set in publication statement')
            # recognized as abbyy input
            self.assert_('Abbyy file' in tei.header.source_description,
                'input should be recognized as Abbyy ocr')
            # brief bibliographic data
            self.assert_(mockvolume.display_label in tei.header.source_description)
            self.assert_(mockvolume.creator[0] in tei.header.source_description)
            self.assert_(mockvolume.date in tei.header.source_description)

            # TODO: check graphic url, spot check text content and coordinates

    def test_pageV1_1(self):
        # page 1.1 - mets/alto content
        page = PageV1_1(Mock()) # use mock for fedora api, since we won't make any calls
        # set mets fixture as page ocr
        page.ocr.content = self.mets_alto
        page.page_order = 3
        with patch('readux.books.models.PageV1_1.volume') as mockvolume:
            mockvolume.uriref = rdflib.URIRef('vol:1')
            mockvolume.display_label = 'Mabel Meredith'
            mockvolume.volume = None
            mockvolume.creator = ['Townley, Arthur']
            mockvolume.date = '1863'

            # update ocr xml with ids
            page.add_ocr_ids()

            tei = page.generate_tei()
            # NOTE: uncomment to see generated tei
            # print tei.serialize()

            # should be generating valid tei
            # if not tei.schema_valid():
               # print tei.schema_validation_errors()
            self.assertTrue(tei.schema_valid())

            # NOTE: not testing header details that are the same for both
            # outputs and already checked in previous test

            # - page identifier carried through from the ocr
            page_id = page.ocr.content.node.xpath('//alto:Page/@xml:id',
                namespaces={'alto': 'http://www.loc.gov/standards/alto/ns-v2#'})[0]
            self.assertEqual(page_id, tei.page.id,
                'xml:id should be copied from mets/alto to tei')
            # recognized as mets/alto
            self.assert_('Mets/Alto file' in tei.header.source_description,
                'input should be recognized as mets/alto ocr')

        # TODO: spot check text content and coordinates


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


class IIIFImageClientTest(TestCase):

    api_endpoint = 'http://imgserver.co/'
    image_id = 'img1'

    def setUp(self):
        self.img = iiif.IIIFImageClient(api_endpoint=self.api_endpoint,
            image_id=self.image_id)

    def test_defaults(self):
        # default image url
        self.assertEqual('%s%s/full/full/0/default.jpg' % \
            (self.api_endpoint, self.image_id), unicode(self.img))
        # info url
        self.assertEqual('%s%s/info.json' % \
            (self.api_endpoint, self.image_id), self.img.info())

    def test_size(self):
        width, height, percent = 100, 150, 50
        # width only
        self.assertEqual('%s%s/full/%s,/0/default.jpg' % \
            (self.api_endpoint, self.image_id, width),
            unicode(self.img.size(width=width)))
        # height only
        self.assertEqual('%s%s/full/,%s/0/default.jpg' % \
            (self.api_endpoint, self.image_id, height),
            unicode(self.img.size(height=height)))
        # width and height
        self.assertEqual('%s%s/full/%s,%s/0/default.jpg' % \
            (self.api_endpoint, self.image_id, width, height),
            unicode(self.img.size(width=width, height=height)))
        # exact width and height
        self.assertEqual('%s%s/full/!%s,%s/0/default.jpg' % \
            (self.api_endpoint, self.image_id, width, height),
            unicode(self.img.size(width=width, height=height, exact=True)))
        # percent
        self.assertEqual('%s%s/full/pct:%s/0/default.jpg' % \
            (self.api_endpoint, self.image_id, percent),
            unicode(self.img.size(percent=percent)))

    def test_format(self):
        png = self.img.format('png')
        jpg = self.img.format('jpg')
        gif = self.img.format('gif')
        self.assert_(unicode(png).endswith('.png'))
        self.assert_(unicode(jpg).endswith('.jpg'))
        self.assert_(unicode(gif).endswith('.gif'))

        self.assertRaises(Exception, self.img.format, 'bogus')
