import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch, Mock
import re
import rdflib
from rdflib import RDF
from urllib import urlencode, unquote

from eulxml.xmlmap import load_xmlobject_from_file, XmlObject
from eulfedora.server import Repository
from piffle import iiif

from readux.annotations.models import Annotation
from readux.books import abbyyocr
from readux.books.models import SolrVolume, Volume, VolumeV1_0, Book, BIBO, \
    DC, Page, PageV1_1



FIXTURE_DIR = os.path.join(settings.BASE_DIR, 'readux', 'books', 'fixtures')


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
        self.assert_(url.startswith('https://'))
        self.assert_(url.endswith(reverse('books:text', kwargs={'pid': volume.pid})))
        current_site = Site.objects.get_current()
        self.assert_(current_site.domain in url)

    def test_voyant_url(self):
        # Volume with English Lang
        volume1 = SolrVolume(label='ocn460678076_V.1',
                             pid='testpid:1234', language='eng')
        url = volume1.voyant_url()

        self.assert_(urlencode({'corpus': volume1.pid}) in url,
            'voyant url should include volume pid as corpus identifier')
        self.assert_(urlencode({'archive': volume1.fulltext_absolute_url()}) in url,
            'voyant url should include volume fulltext url as archive')
        self.assert_(urlencode({'stopList': 'stop.en.taporware.txt'}) in url,
            'voyant url should not include english stopword list when volume is in english')

        # volume language is French
        volume2 = SolrVolume(label='ocn460678076_V.1',
                             pid='testpid:1235', language='fra')
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
        annotations = vol.annotations().visible_to(testuser)
        self.assertEqual(3, annotations.count())
        self.assert_(sup2 not in annotations)

        annotations = vol.annotations().visible_to(testadmin)
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
        self.vol.pid = 'rdxtest:4606'

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
                ocr_xml = load_xmlobject_from_file(os.path.join(FIXTURE_DIR,
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
            ocr_xml = load_xmlobject_from_file(os.path.join(FIXTURE_DIR,
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
            ocr_xml = load_xmlobject_from_file(os.path.join(FIXTURE_DIR,
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
            ocr_xml = load_xmlobject_from_file(os.path.join(FIXTURE_DIR,
                'abbyyocr_fr8v2.xml'))
            mockocr.content = ocr_xml

            self.assertFalse(self.vol.ocr_has_ids)
            self.vol.add_ocr_ids()
            self.assertTrue(self.vol.ocr_has_ids)

class PageV1_1Test(TestCase):
    metsalto_doc = os.path.join(FIXTURE_DIR, 'mets_alto.xml')

    def setUp(self):
        self.mets_alto = load_xmlobject_from_file(self.metsalto_doc, XmlObject)

    def test_ocr_ids(self):
        page = PageV1_1(Mock()) # use mock for fedora api, since we won't make any calls
        page.pid = 'rdxtest:4607'

        with patch.object(page, 'ocr') as mockocr:
            mockocr.exists = True
            mockocr.content = self.mets_alto
            self.assertFalse(page.ocr_has_ids)
            page.add_ocr_ids()
            self.assertTrue(page.ocr_has_ids)

class AbbyyOCRTestCase(TestCase):

    fr6v1_doc = os.path.join(FIXTURE_DIR, 'abbyyocr_fr6v1.xml')
    fr8v2_doc = os.path.join(FIXTURE_DIR, 'abbyyocr_fr8v2.xml')
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
