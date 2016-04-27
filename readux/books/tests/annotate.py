# -*- coding: UTF-8 -*-
import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from eulxml.xmlmap import load_xmlobject_from_file
import json
from lxml import etree
import os.path

from readux import __version__
from readux.annotations.models import Annotation
from readux.books import tei
from readux.books.annotate import annotation_to_tei, insert_anchor, \
    annotated_tei, consolidate_bibliography
from readux.books.tests.models import FIXTURE_DIR


class AnnotatedTei(TestCase):

    def test_annotation_to_tei(self):
        teidoc = load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'teifacsimile.xml'),
            tei.AnnotatedFacsimile)

        note = Annotation(text="Here's the thing", quote="really",
            extra_data=json.dumps({'sample data': 'foobar',
                'tags': ['test', 'one', 'two']}))

        teinote = annotation_to_tei(note, teidoc)
        self.assert_(isinstance(teinote, tei.Note))
        self.assertEqual('annotation-%s' % note.id, teinote.id)
        self.assert_(teinote.href.endswith(note.get_absolute_url()))
        self.assertEqual(note.text, teinote.paragraphs[0])

        # todo: add a schema validation once we get the output to be valid
        # teidoc.schema_valid()
        # access errors with teidoc.schema_validation_errors()

        # annotation user should be set as note response
        user = get_user_model()(username='an_annotator')
        user.save()
        note.user = user
        teinote = annotation_to_tei(note, teidoc)
        self.assertEqual(user.username, teinote.resp)

        # tags should be set as interp ids ana attribute
        for tag in note.info()['tags']:
            self.assert_('#%s' % tag in teinote.ana)

        # test that markdown formatting is coming through
        footnote = '''Footnotes[^1] have a label and content.

[^1]: This is some footnote content.'''
        note.text = footnote
        teinote = annotation_to_tei(note, teidoc)
        self.assert_('<ref target="#fn1" type="noteAnchor">1</ref>' in
            teinote.serialize())

        # markdown should be included in a code element
        self.assertEqual(note.text, teinote.markdown)

        # related page references
        rel_pages = [
            'http://testpid.co/ark:/1234/11',
            'http://testpid.co/ark:/1234/22',
            'http://testpid.co/ark:/1234/qq'
        ]
        note.extra_data = json.dumps({'related_pages': rel_pages})
        teinote = annotation_to_tei(note, teidoc)
        self.assertEqual(len(rel_pages), len(teinote.related_pages))
        # first ark has a corresponding id in the fixture, should be converted
        self.assertEqual('#%s' % teidoc.page_id_by_xlink(rel_pages[0]),
            teinote.related_pages[0].target)
        for idx in range(len(rel_pages)):
            self.assertEqual(rel_pages[idx], teinote.related_pages[idx].text)


    zotero_note = Annotation(text=u'''update test ing la lala ([Jockers and Mimno 2013](#zotero-MUXAEE89))
more content ([Underwood and Sellers 2012](#zotero-7CBCH6E8))
la la la foo bar lala
---
### Works Cited
* <a name="zotero-MUXAEE89"></a>Jockers, Matthew L., and David Mimno. “Significant Themes in 19th-Century Literature.” <i>Poetics</i> 41, no. 6 (December 2013): 750–69. doi:10.1016/j.poetic.2013.08.005.
* <a name="zotero-7CBCH6E8"></a>Underwood, Ted, and Jordan Sellers. “The Emergence of Literary Diction.” <i>Journal of Digital Humanities</i>, June 26, 2012. http://journalofdigitalhumanities.org/1-2/the-emergence-of-literary-diction-by-ted-underwood-and-jordan-sellers/.''',
            quote="really",
            extra_data=json.dumps({'citations': [
    '<biblStruct xmlns="http://www.tei-c.org/ns/1.0" type="webpage" xml:id="zoteroItem-http://zotero.org/users/758030/items/7CBCH6E8" corresp="http://zotero.org/users/758030/items/7CBCH6E8"><monogr><title level="m">The Emergence of Literary Diction</title><author><forename>Ted</forename><surname>Underwood</surname></author><author><forename>Jordan</forename><surname>Sellers</surname></author><imprint><date>2012</date><note type="accessed">2015-05-09T22:02:51Z</note><note type="url">http://journalofdigitalhumanities.org/1-2/the-emergence-of-literary-diction-by-ted-underwood-and-jordan-sellers/</note></imprint></monogr></biblStruct>',
    '<biblStruct xmlns="http://www.tei-c.org/ns/1.0" type="journalArticle" xml:id="zoteroItem-http://zotero.org/users/758030/items/MUXAEE89" corresp="http://zotero.org/users/758030/items/MUXAEE89"><analytic><title level="a">Significant themes in 19th-century literature</title><author><forename>Matthew L.</forename><surname>Jockers</surname></author><author><forename>David</forename><surname>Mimno</surname></author></analytic><monogr><title level="j">Poetics</title><imprint><biblScope unit="volume">41</biblScope><biblScope unit="issue">6</biblScope><biblScope unit="page">750-769</biblScope><date>2013</date><note type="accessed">2016-01-24T02:44:56Z</note><note type="url">http://linkinghub.elsevier.com/retrieve/pii/S0304422X13000673</note></imprint></monogr><idno type="ISSN">0304422X</idno><idno type="DOI">10.1016/j.poetic.2013.08.005</idno></biblStruct>'
    ]}))
    def test_annotation_citation_to_tei(self):
        teidoc = load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'teifacsimile.xml'),
            tei.AnnotatedFacsimile)

        teinote = annotation_to_tei(self.zotero_note, teidoc)
        # print teinote.serialize(pretty=True)
        # number of citations should match
        self.assertEqual(len(self.zotero_note.extra_data['citations']),
                         len(teinote.citations))
        # minimal inspection to check that values carried through as expected
        self.assertEqual('webpage', teinote.citations[0].type)
        self.assertEqual('journalArticle', teinote.citations[1].type)

        self.assertEqual('zotero-7CBCH6E8', teinote.citations[0].id)
        self.assertEqual('zotero-MUXAEE89', teinote.citations[1].id)


    def test_insert_anchor(self):
        def get_test_elements():
            div = etree.fromstring('''<div>
                <p>Sample text to insert anchors into</p>
            </div>''')
            element = div.xpath('//p')[0]
            return div, element

        div, element = get_test_elements()
        anchor = etree.fromstring('<anchor/>')
        # insert anchor at 0 index relative to paragraph
        insert_anchor(element, anchor, 0)

        # 0 index, anchor should be *before* tag
        self.assertEqual('anchor', element.getprevious().tag)

        div, element = get_test_elements()
        # insert anchor in the middle of the paragraph
        insert_anchor(element, anchor, 11)
        # anchor element should be a child of p tag
        self.assert_(anchor in element.getchildren())
        # text should be split before and after anchor
        self.assertEqual('Sample text', element.text)
        self.assertEqual(' to insert anchors into', anchor.tail)

        div, element = get_test_elements()
        anchor = etree.fromstring('<anchor/>')
        # insert anchor at the end of the paragraph
        insert_anchor(element, anchor, 35)
        # 0 index, anchor should be after tag
        self.assertEqual('anchor', element.getnext().tag)

    def test_annotated_tei(self):
        # create annotation with a user
        user = get_user_model()(username='an_annotator',
            first_name="Anne", last_name="O'Tater")
        user.save()
        page_uri = "http://readux.co/books/pages/some:1/"
        note = Annotation(text="Here's the thing", quote="really",
            uri=page_uri,
            extra_data=json.dumps({
                'sample data': 'foobar',
                'tags': ['test', 'one', 'two'],
                'ranges': [
                    {'start': '//div[@id="fnstr.idm320760248608"]/span[1]',
                     'end': '//div[@id="fnstr.idm320760242176"]/span[1]',
                     'startOffset': 0,
                     'endOffset': 6
                     }
                ],
                'ark': page_uri
                }),
            user=user)
        note.save()
        imagenote = Annotation(text='interesting image detail', uri=page_uri,
            user=user,
            extra_data=json.dumps({
                'image_selection': {
                    # NOTE: image src currently not checked when generating annotated tei
                    'h': '20.73%',
                    'w': '14.70%',
                    'y': '62.42%',
                    'x': '61.60%'
                    },
                'ark': page_uri
                })
            )
        imagenote.save()

        # use page tei fixture as starting point
        title = 'Lecoq'
        teidoc = load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'teifacsimile.xml'),
            tei.AnnotatedFacsimile)
        teidoc.title = title
        teidoc.page.href = page_uri
        del teidoc.responsible_names[0]  # remove empty resp name from fixture

        annotei = annotated_tei(teidoc, Annotation.objects.all())
        self.assert_(isinstance(annotei, tei.AnnotatedFacsimile),
            'annotated_tei should return an insance of tei.AnnotatedFacsimile')

        # title should be updated, split into main and subtitle parts
        self.assertEqual(title, annotei.main_title)
        self.assertEqual(', an annotated digital edition', annotei.subtitle)
        self.assertEqual('annotated by', annotei.responsibility)
        # annotation authors should be added in resp statement
        self.assertEqual(user.username, annotei.responsible_names[0].id)
        self.assertEqual(user.get_full_name(), annotei.responsible_names[0].value)

        # publication statement should include readux version, current date
        self.assert_('Annotated TEI generated by Readux' in annotei.pubstmt.desc)
        self.assert_(__version__ in annotei.pubstmt.desc)
        today = datetime.date.today()
        self.assertEqual(today, annotei.pubstmt.date)
        self.assertEqual(today, annotei.pubstmt.date_normal)

        # tei annotation should be added to body for text note
        self.assertEqual('annotation-%s' % note.id, annotei.annotations[0].id)
        # start/end highlight anchors should be added to facsimile
        self.assert_(annotei.node.xpath('//tei:anchor[@xml:id="highlight-start-%s"]' % note.id,
            namespaces=tei.Zone.ROOT_NAMESPACES))
        self.assert_(annotei.node.xpath('//tei:anchor[@xml:id="highlight-end-%s"]' % note.id,
            namespaces=tei.Zone.ROOT_NAMESPACES))

        # tei annotation should be added to body for image note
        self.assertEqual('annotation-%s' % imagenote.id, annotei.annotations[1].id)
        # zone added for image highlight
        self.assert_(annotei.node.xpath('//tei:zone[@xml:id="highlight-%s"][@type="image-annotation-highlight"]' % imagenote.id,
            namespaces=tei.Zone.ROOT_NAMESPACES))

        # tags added to back as interp group
        self.assertEqual('test', annotei.tags.interp[0].id)
        self.assertEqual('test', annotei.tags.interp[0].value)

        # encoding desc should be present
        self.assert_(annotei.encoding_desc)

    def test_consolidate_bibl(self):
        teidoc = load_xmlobject_from_file(os.path.join(FIXTURE_DIR,
                                                       'teifacsimile.xml'),
                                          tei.AnnotatedFacsimile)
        teinote = annotation_to_tei(self.zotero_note, teidoc)
        teidoc.annotations.append(teinote)
        consolidate_bibliography(teidoc)

        self.assertEqual(2, len(teidoc.citations),
            'annotation citations should be present in main document bibl')
        teinote = teidoc.annotations[0]
        self.assertEqual(0, len(teinote.citations),
            'citations should not be present on individual annotation')
        self.assertEqual(None, teinote.works_cited)
        self.assertEqual(None, teinote.zotero_items)
        self.assertEqual(None, teinote.works_cited_milestone)
        teinote_xml = teinote.serialize()
        self.assertFalse('<item><anchor xml:id="zotero-' in teinote_xml)
        self.assertFalse('<listBibl/>' in teinote_xml)

        # repeated zotero ids should only appear once in document bibl
        # load the same note and add it again
        teinote = annotation_to_tei(self.zotero_note, teidoc)
        teidoc.annotations.append(teinote)
        consolidate_bibliography(teidoc)
        self.assertEqual(2, len(teidoc.citations),
            'citations repeated in annotations should only appear once')
