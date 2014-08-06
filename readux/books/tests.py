import os
from datetime import datetime
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch, Mock, NonCallableMock, NonCallableMagicMock
import rdflib
from rdflib import RDF

from eulxml.xmlmap import load_xmlobject_from_file
from eulfedora.server import Repository
from eulfedora.util import RequestFailed

from readux.books import abbyyocr
from readux.books.models import SolrVolume, Volume, Book, BIBO, DC

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

class VolumeTest(TestCase):

    def setUp(self):
        # use uningested objects for testing purposes
        repo = Repository()
        self.vol = repo.get_object(type=Volume)
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


class BookViewsTest(TestCase):

    @patch('readux.books.views.Repository')
    @patch('readux.books.views.raw_datastream')
    def test_pdf(self, mockraw_ds, mockrepo):
        mockobj = Mock()
        mockobj.pid = 'vol:1'
        mockobj.label = 'ocm30452349_1908'
        mockrepo.return_value.get_object.return_value = mockobj
        # to support for last modified conditional
        mockobj.pdf.created = datetime.now()

        pdf_url = reverse('books:pdf', kwargs={'pid': mockobj.pid})
        response = self.client.get(pdf_url)

        # only check custom logic implemented here, via mocks
        # (not testing eulfedora.views.raw_datastream logic)
        self.assertEqual(mockraw_ds.return_value.render(), response,
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

        # fedora error should 404
        mockresponse = Mock()
        mockresponse.status = 500
        mockresponse.reason = 'server error'
        mockraw_ds.side_effect = RequestFailed(mockresponse, '')
        response = self.client.get(pdf_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected %s for %s when there is a fedora error, got %s' % \
            (expected, pdf_url, got))

    @patch('readux.books.views.Paginator', spec=Paginator)
    @patch('readux.books.views.solr_interface')
    def test_search(self, mocksolr_interface, mockpaginator):

        # no search terms - invalid form
        search_url = reverse('books:search')
        response = self.client.get(search_url)
        self.assertContains(response, 'Please enter one or more search terms')

        mocksolr = mocksolr_interface.return_value
        # simulate sunburnt's fluid interface
        mocksolr.query.return_value = mocksolr.query
        for method in ['query', 'facet_by', 'sort_by', 'field_limit',
                       'exclude', 'filter', 'join', 'paginate', 'results_as']:
            getattr(mocksolr.query, method).return_value = mocksolr.query

        # set up mock results for collection query and facet counts
        solr_result = NonCallableMagicMock(spec_set=['__iter__', 'facet_counts'])
        # *only* mock iter, to avoid weirdness with django templates & callables
        solr_result.__iter__.return_value = [
            {'pid': 'vol:1', 'title': 'Lecoq, the detective'},
            {'pid': 'vol:2', 'title': 'Mabel Meredith'},
        ]
        mocksolr.query.__iter__.return_value = iter(solr_result)
        mocksolr.count.return_value = 2
        # mock facets
        # solr_result.facet_counts.facet_fields = {
        #     'collection_label_facet': [('Civil War Literature', 2), ('Yellowbacks', 4)]
        # }

        # use a noncallable for the pagination result that is used in the template
        # because passing callables into django templates does weird things
        mockpage = NonCallableMock()
        mockpaginator.return_value.page.return_value = mockpage
        results = NonCallableMagicMock(spec=['__iter__', 'facet_counts'])
        results.__iter__.return_value = iter(solr_result)
        results.facet_counts.facet_fields = {
            'collection_label_facet': [('Emory Yearbooks', 1), ('Yellowbacks', 4)]
        }

        mockpage.object_list = results
        mockpage.has_other_pages = False
        mockpage.paginator.count = 2
        mockpage.paginator.page_range = [1]

        # query with search terms
        response = self.client.get(search_url, {'keyword': 'yellowbacks'})

        mocksolr.query.filter.assert_called_with(content_model=Volume.VOLUME_CONTENT_MODEL)
        # because of creator/title search boosting, actual query is a little difficult to test
        mocksolr.Q.assert_any_call('yellowbacks')
        mocksolr.Q.assert_any_call(creator='yellowbacks')
        mocksolr.Q.assert_any_call(title='yellowbacks')
        # not sure how to test query on Q|Q**3|Q**3
        mocksolr.query.field_limit.assert_called_with(['pid', 'title', 'label',
            'language', 'creator', 'date', 'hasPrimaryImage', 'page_count',
            'collection_id', 'collection_label'], score=True)

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
            self.assertContains(response, reverse('books:pdf', kwargs={'pid': item['pid']}),
                msg_prefix='link to pdf should be included in response')
            self.assertContains(response,
                '<abbr class="unapi-id" title="%s"></abbr>' % item['pid'],
                msg_prefix='unapi item id for %s should be included to allow zotero harvest' \
                           % item['pid'])

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


    @patch('readux.books.views.Repository')
    def test_text(self, mockrepo):
        mockobj = Mock()
        mockobj.pid = 'vol:1'
        mockobj.label = 'ocm30452349_1908'
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
        mockobj.ocr.exists = False
        response = self.client.get(text_url)
        self.assertEqual(404, response.status_code,
            'text view should 404 if ocr datastream does not exist')
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

        # non-existent should 404
        mockobj.exists = False
        response = self.client.get(vol_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected %s for %s when object does not exist, got %s' % \
            (expected, vol_url, got))
        # exists but isn't a volume - should also 404
        mockobj.exists = True
        mockobj.has_requisite_content_models = False
        response = self.client.get(vol_url)
        expected, got = 404, response.status_code
        self.assertEqual(expected, got,
            'expected %s for %s when object is not a volume, got %s' % \
            (expected, vol_url, got))

    @patch('readux.books.views.Repository')
    @override_settings(DEBUG=True)  # required so local copy of not-found image will be used
    def test_page_image(self, mockrepo):
        mockobj = Mock()
        mockobj.pid = 'page:1'
        mockrepo.return_value.get_object.return_value = mockobj

        url = reverse('books:page-thumbnail', kwargs={'pid': mockobj.pid})

        # no image datastream
        mockobj.image.exists = False
        response = self.client.get(url)
        self.assertEqual(404, response.status_code,
            'page-image should 404 when image datastream doesn\'t exist')
        with open(os.path.join(settings.STATICFILES_DIRS[0], 'img', 'notfound_thumbnail.png')) as thumb:
            self.assertEqual(thumb.read(), response.content,
                '404 should serve out static not found image')
        self.assertEqual('image/png', response['Content-Type'],
            '404 should be served as image/png')

        # image exists
        mockobj.image.exists = True
        mockobj.image.checksum_type = 'MD5'
        mockobj.image.checksum = 'not-a-real-checksum'
        mockobj.get_region.return_value = 'test thumbnail content'
        response = self.client.get(url)
        mockobj.get_region.assert_called_with(scale=300)
        self.assertEqual(mockobj.get_region.return_value, response.content)
        self.assertEqual(mockobj.image.checksum, response['ETag'])
        self.assertEqual('image/jpeg', response['Content-Type'],
            '404 should be served as image/jpeg')

        # error generating image
        mockobj.get_region.side_effect = RequestFailed(Mock(status=500,
            reason='unknown error'), content='stack trace here...')
        response = self.client.get(url)
        self.assertEqual(500, response.status_code,
            'page-image should return 500 when Fedora error is a 500')
        with open(os.path.join(settings.STATICFILES_DIRS[0], 'img', 'notfound_thumbnail.png')) as thumb:
            self.assertEqual(thumb.read(), response.content,
                'fedora error should serve out static not found image')


class AbbyyOCRTestCase(TestCase):

    fixture_dir = os.path.join(settings.BASE_DIR, 'readux', 'books', 'fixtures')

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
