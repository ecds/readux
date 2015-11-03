from django.contrib.auth import get_user_model
from django.test import TestCase
import json

from readux.annotations.models import Annotation
from readux.books.annotate import annotation_to_tei, markdown_to_tei
from readux.books.models import TeiNote

class AnnotatedTei(TestCase):

    def test_markdown_to_tei(self):
        # several example inputs taken from markdown documentation at
        # https://daringfireball.net/projects/markdown/syntax#block

        # single paragraph
        ptext = 'Single paragraph'
        self.assertEqual('<p>%s</p>' % ptext,
            markdown_to_tei(ptext))
        # two paragraphs
        # ptext2 = 'Second paragraph'
        # print '%s\n\n%s\n' % (ptext, ptext2)
        # print markdown_to_tei('%s\n\n%s' % (ptext, ptext2))
        # self.assertEqual('<p>%s</p><p>%s</p>' % (ptext, ptext2),
        #     markdown_to_tei('%s\n%s' % (ptext, ptext2)))

        # emphasis - bold
        self.assertEqual('<p>a <emph rend="bold">bold</emph> statement</p>',
            markdown_to_tei('a **bold** statement'))
        # emphasis - italic
        self.assertEqual('<p>an <emph rend="italic">emphatic</emph> statement</p>',
            markdown_to_tei('an *emphatic* statement'))

        self.assertEqual('<list><item>Red</item><item>Green</item><item>Blue</item></list>',
            markdown_to_tei(unordered_list))
        # list - ordered
        ordered_list = '1. Red\n' + \
            '2. Green\n' + \
            '3. Blue'
        self.assertEqual('<list rend="numbered"><item>Red</item><item>Green</item><item>Blue</item></list>',
            markdown_to_tei(ordered_list))

        # TODO: headers
        # This is an H1
        ## This is an H2
        ###### This is an H6

        blockquote = '\n'.join([
            '> This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet',
            '> consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.',
            '> Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.',
            '> ',
            '> Donec sit amet nisl. Aliquam semper ipsum sit amet velit. Suspendisse',
            '> id sem consectetuer libero luctus adipiscing.'])
        tei_blockquote = markdown_to_tei(blockquote)
        self.assert_(tei_blockquote.startswith('<quote><p>This is a blockquote'))
        self.assert_('risus.</p><p>Donec' in tei_blockquote)
        self.assert_(tei_blockquote.endswith('adipiscing.</p></quote>'))

        # link
        # still TODO in tei renderer
        # linktext = 'This is [an example](http://example.com/ "Title") inline link.'
        # print markdown_to_tei(linktext)
        # linktext = '[This link](http://example.net/) has no title attribute.'
        # print markdown_to_tei(linktext)

        # image
        imglink = '![Alt text](/path/to/img.png)'
        tei_imglink = markdown_to_tei(imglink)
        self.assert_('<media' in tei_imglink)
        self.assert_(' mimetype="image/png"' in tei_imglink)
        self.assert_(' url="/path/to/img.png"' in tei_imglink)
        self.assert_('<desc><p>Alt text</p></desc>' in tei_imglink)

        imglink_title = '![Alt text](/path/to/img.jpg "Optional title")'
        tei_imglink_title = markdown_to_tei(imglink_title)
        self.assert_('<desc><head>Optional title</head><p>Alt text</p></desc>'
            in tei_imglink_title)

        # footnote
        footnote = '''Footnotes[^1] have a label and content.

[^1]: This is some footnote content.'''
        tei_footnote = markdown_to_tei(footnote)
        self.assert_('<p>Footnotes<ref target="#fn1" type="noteAnchor">1</ref> have' in tei_footnote)
        self.assert_('<note xml:id="fn1" type="footnote"><p>This is some footnote content.</p></note>'
            in tei_footnote)



    def test_annotation_to_tei(self):
        note = Annotation(text="Here's the thing", quote="really",
            extra_data=json.dumps({'sample data': 'foobar'}))

        teinote = annotation_to_tei(note)
        self.assert_(isinstance(teinote, TeiNote))
        self.assertEqual(note.get_absolute_url(), teinote.id)
        self.assertEqual(note.text, teinote.paragraphs[0])

        # annotation user should be set as note response
        user = get_user_model()(username='an_annotator')
        note.user = user
        teinote = annotation_to_tei(note)
        self.assertEqual(user.username, teinote.resp)

        # test that markdown formatting is coming through
        footnote = '''Footnotes[^1] have a label and content.

[^1]: This is some footnote content.'''
        note.text = footnote
        teinote = annotation_to_tei(note)
        self.assert_('<ref target="#fn1" type="noteAnchor">1</ref>' in
            teinote.serialize())




