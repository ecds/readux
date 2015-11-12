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
    annotated_tei
from readux.books.tests.models import FIXTURE_DIR


class AnnotatedTei(TestCase):

    def test_annotation_to_tei(self):
        note = Annotation(text="Here's the thing", quote="really",
            extra_data=json.dumps({'sample data': 'foobar',
                'tags': ['test', 'one', 'two']}))

        teinote = annotation_to_tei(note)
        self.assert_(isinstance(teinote, tei.Note))
        self.assertEqual('annotation-%s' % note.id, teinote.id)
        self.assert_(teinote.href.endswith(note.get_absolute_url()))
        self.assertEqual(note.text, teinote.paragraphs[0])

        # annotation user should be set as note response
        user = get_user_model()(username='an_annotator')
        note.user = user
        teinote = annotation_to_tei(note)
        self.assertEqual(user.username, teinote.resp)

        # tags should be set as interp ids ana attribute
        for tag in note.info()['tags']:
            self.assert_('#%s' % tag in teinote.ana)

        # test that markdown formatting is coming through
        footnote = '''Footnotes[^1] have a label and content.

[^1]: This is some footnote content.'''
        note.text = footnote
        teinote = annotation_to_tei(note)
        self.assert_('<ref target="#fn1" type="noteAnchor">1</ref>' in
            teinote.serialize())

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
                     'endOffset': 6}
                ]
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
                    'x': '61.60%'}
                })
            )
        imagenote.save()

        # use page tei fixture as starting point
        title = 'Lecoq'
        teidoc = load_xmlobject_from_file(os.path.join(FIXTURE_DIR, 'teifacsimile.xml'),
            tei.Facsimile)
        teidoc.title = title
        teidoc.page.href = page_uri

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



