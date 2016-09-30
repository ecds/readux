import os
from eulxml.xmlmap import XmlObject, load_xmlobject_from_file, \
    load_xmlobject_from_string
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock, patch
import rdflib

from readux.books import abbyyocr, tei
from readux.books.models import PageV1_0, VolumeV1_0, PageV1_1, \
    VolumeV1_1
from readux.books.tests.models import FIXTURE_DIR


class TeiFacsimileTest(TestCase):

    def setUp(self):
        # tei generated from mets alto
        self.alto_tei = load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'teifacsimile.xml'),
            tei.Facsimile)
        # tei generated from abbyy ocr
        self.abbyy_tei = load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'teifacsimile_abbyy.xml'),
            tei.Facsimile)

    def test_basic_properties_alto(self):
        self.assert_(isinstance(self.alto_tei.page, tei.Zone))
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
        self.assert_(isinstance(self.alto_tei.word_zones[0], tei.Zone))

    def test_basic_properties_abbyy(self):
        self.assert_(isinstance(self.abbyy_tei.page, tei.Zone))
        # quick check page size params coming through
        self.assertEqual(0, self.abbyy_tei.page.ulx)
        self.assertEqual(0, self.abbyy_tei.page.uly)
        self.assertEqual(2182, self.abbyy_tei.page.lrx)
        self.assertEqual(3093, self.abbyy_tei.page.lry)
        # no easy way to check type (nodelist), so just check that it is non-false
        self.assert_(self.abbyy_tei.lines,
            'tei facsimile should have a list of lines')
        self.assert_(isinstance(self.abbyy_tei.lines[0], tei.Zone))
        # check line content
        self.assertEqual('Presentation', self.abbyy_tei.lines[0].text)

    def test_page_id_by_xlink(self):
        uri = 'http://testpid.co/ark:/1234/11'
        teidoc = tei.AnnotatedFacsimile(self.alto_tei.node)
        page_id = teidoc.page_id_by_xlink(uri)
        self.assertEqual(self.alto_tei.page_list[0].id, page_id)
        # no match, should return none
        uri = '%sqqq' % uri
        self.assertEqual(None, teidoc.page_id_by_xlink(uri))


@override_settings(TEI_DISTRIBUTOR='Readux Test Publications')
class OCRtoTEIFacsimileXSLTest(TestCase):

    fr6v1_doc = os.path.join(FIXTURE_DIR, 'abbyyocr_fr6v1.xml')
    fr8v2_doc = os.path.join(FIXTURE_DIR, 'abbyyocr_fr8v2.xml')
    metsalto_doc = os.path.join(FIXTURE_DIR, 'mets_alto.xml')

    def setUp(self):
        self.fr6v1 = load_xmlobject_from_file(self.fr6v1_doc, abbyyocr.Document)
        self.fr8v2 = load_xmlobject_from_file(self.fr8v2_doc, abbyyocr.Document)
        self.mets_alto = load_xmlobject_from_file(self.metsalto_doc, XmlObject)

    def test_pageV1_0(self):
        # page 1.0 - abbyy ocr content

        page = PageV1_0(Mock()) # use mock for fedora api, since we won't make any calls
        page.pid = 'rdxtest:4607'
        page.page_order = 5
        # vol = VolumeV1_0(Mock())
        with patch('readux.books.models.PageV1_0.volume') as mockvolume:
            mockvolume.uriref = rdflib.URIRef('vol:1')
            mockvolume.display_label = 'Mabel Meredith'
            mockvolume.volume = None
            mockvolume.creator = ['Townley, Arthur']
            mockvolume.date = '1863'

            # update fixture xml with ids
            with open(VolumeV1_0.ocr_add_ids_xsl) as xslfile:
                result = self.fr6v1.xsl_transform(filename=xslfile,
                    return_type=unicode)
                fr6v1_with_ids = load_xmlobject_from_string(result,
                    abbyyocr.Document)

            # use the first page with substantial text content as input
            ocr_page = fr6v1_with_ids.pages[5]
            teipage = page.generate_tei(ocr_page)
            # NOTE: uncomment to see generated TEI
            # print tei.serialize()

            # should be generating valid tei
            # if not tei.schema_valid():
                # print tei.schema_validation_errors()
            self.assertTrue(teipage.schema_valid(),
                'generated TEI facsimile should be schema-valid')
            # inspect the tei and check for expected values
            # - page identifier based on page_order value passed in
            self.assertEqual(ocr_page.id, teipage.page.id,
                'tei id should be carried through from ocr xml')
            self.assertEqual(page.display_label, teipage.title,
                'tei title should be set from page diplay label')
            # distributor not mapped in teimap, so just use xpath to check
            self.assertEqual(settings.TEI_DISTRIBUTOR,
                teipage.node.xpath('string(//t:publicationStmt/t:distributor)',
                    namespaces={'t': teipage.ROOT_NS}),
                'configured tei distributor should be set in publication statement')
            # recognized as abbyy input
            self.assert_('Abbyy file' in teipage.header.source_description,
                'input should be recognized as Abbyy ocr')
            # brief bibliographic data
            self.assert_(mockvolume.display_label in teipage.header.source_description)
            self.assert_(mockvolume.creator[0] in teipage.header.source_description)
            self.assert_(mockvolume.date in teipage.header.source_description)

            # TODO: check graphic url, spot check text content and coordinates

    def test_pageV1_1(self):
        # page 1.1 - mets/alto content
        page = PageV1_1(Mock()) # use mock for fedora api, since we won't make any calls
        # set mets fixture as page ocr
        page.ocr.content = self.mets_alto
        page.pid = 'rdxtest:4608'
        page.page_order = 3

        with patch('readux.books.models.PageV1_1.volume') as mockvolume:
            mockvolume.uriref = rdflib.URIRef('vol:1')
            mockvolume.display_label = 'Mabel Meredith'
            mockvolume.volume = None
            mockvolume.creator = ['Townley, Arthur']
            mockvolume.date = '1863'

            # update ocr xml with ids
            page.add_ocr_ids()

            teipage = page.generate_tei()
            # NOTE: uncomment to see generated tei
            # print tei.serialize()

            # should be generating valid tei
            # if not tei.schema_valid():
               # print tei.schema_validation_errors()
            self.assertTrue(teipage.schema_valid())

            # NOTE: not testing header details that are the same for both
            # outputs and already checked in previous test

            # - page identifier carried through from the ocr
            page_id = page.ocr.content.node.xpath('//alto:Page/@xml:id',
                namespaces={'alto': 'http://www.loc.gov/standards/alto/ns-v2#'})[0]
            self.assertEqual(page_id, teipage.page.id,
                'xml:id should be copied from mets/alto to tei')
            # recognized as mets/alto
            self.assert_('Mets/Alto file' in teipage.header.source_description,
                'input should be recognized as mets/alto ocr')

        # TODO: spot check text content and coordinates


