from django.test import TestCase
from readux.books import markdown_tei

class MarkdownTei(TestCase):

    # several example inputs taken from markdown documentation at
    # https://daringfireball.net/projects/markdown/syntax#block

    def test_paragraphs(self):

        # single paragraph
        ptext = 'Single paragraph'
        self.assertEqual('<p>%s</p>' % ptext,
            markdown_tei.convert(ptext))
        # two paragraphs
        ptext2 = 'Second paragraph'
        self.assertEqual('<p>%s</p><p>%s</p>' % (ptext, ptext2),
            markdown_tei.convert('%s\n\n%s' % (ptext, ptext2)))

    def test_emphasis(self):

        # emphasis - bold
        self.assertEqual('<p>a <emph rend="bold">bold</emph> statement</p>',
            markdown_tei.convert('a **bold** statement'))
        # emphasis - italic
        self.assertEqual('<p>an <emph rend="italic">emphatic</emph> statement</p>',
            markdown_tei.convert('an *emphatic* statement'))

    def test_lists(self):

        # list - unordered
        unordered_list = '* Red\n' + \
            '* Green\n' + \
            '* Blue'
        self.assertEqual('<list><item>Red</item><item>Green</item><item>Blue</item></list>',
            markdown_tei.convert(unordered_list))
        # list - ordered
        ordered_list = '1. Red\n' + \
            '2. Green\n' + \
            '3. Blue'
        self.assertEqual('<list rend="numbered"><item>Red</item><item>Green</item><item>Blue</item></list>',
            markdown_tei.convert(ordered_list))

    def test_headers(self):

        # headers
        self.assertEqual('<head type="level1">This is an H1</head>',
            markdown_tei.convert('# This is an H1'))
        self.assertEqual('<head type="level2">This is an H2</head>',
            markdown_tei.convert('## This is an H2'))
        self.assertEqual('<head type="level6">This is an H6</head>',
            markdown_tei.convert('###### This is an H6'))

        # horizontal rule
        self.assertEqual('<milestone rend="horizontal-rule"/>',
            markdown_tei.convert('* * *'))

    def test_blockquote(self):

        blockquote = '\n'.join([
            '> This is a blockquote with two paragraphs. Lorem ipsum dolor sit amet',
            '> consectetuer adipiscing elit. Aliquam hendrerit mi posuere lectus.',
            '> Vestibulum enim wisi, viverra nec, fringilla in, laoreet vitae, risus.',
            '> ',
            '> Donec sit amet nisl. Aliquam semper ipsum sit amet velit. Suspendisse',
            '> id sem consectetuer libero luctus adipiscing.'])
        tei_blockquote = markdown_tei.convert(blockquote)
        self.assert_(tei_blockquote.startswith('<quote><p>This is a blockquote'))
        self.assert_('risus.</p><p>Donec' in tei_blockquote)
        self.assert_(tei_blockquote.endswith('adipiscing.</p></quote>'))

    def test_links(self):
        # link
        linktext = 'This is [an example](http://example.com/ "Title") inline link.'
        self.assertEqual('<p>This is <ref target="http://example.com/" n="Title">an example</ref> inline link.</p>',
            markdown_tei.convert(linktext))
        linktext = '[This link](http://example.net/) has no title attribute.'
        self.assertEqual('<p><ref target="http://example.net/">This link</ref> has no title attribute.</p>',
            markdown_tei.convert(linktext))

    def test_images(self):
        # image
        imglink = '![Alt text](/path/to/img.png)'
        tei_imglink = markdown_tei.convert(imglink)
        self.assert_('<media' in tei_imglink)
        self.assert_(' mimetype="image/png"' in tei_imglink)
        self.assert_(' url="/path/to/img.png"' in tei_imglink)
        self.assert_('<desc><p>Alt text</p></desc>' in tei_imglink)

        imglink_title = '![Alt text](/path/to/img.jpg "Optional title")'
        tei_imglink_title = markdown_tei.convert(imglink_title)
        self.assert_('<desc><head>Optional title</head><p>Alt text</p></desc>'
            in tei_imglink_title)

    def test_footnotes(self):
        # footnote
        footnote = '''Footnotes[^1] have a label and content.

[^1]: This is some footnote content.'''
        tei_footnote = markdown_tei.convert(footnote)
        self.assert_('<p>Footnotes<ref target="#fn1" type="noteAnchor">1</ref> have' in tei_footnote)
        self.assert_('<note xml:id="fn1" type="footnote"><p>This is some footnote content.</p></note>'
            in tei_footnote)

    def test_tables(self):
        # table
        table = '''
Firstly  | Secondly
-------  | --------
A.1  | A.2
B.1  | B.2
'''
        tei_table = markdown_tei.convert(table)
        self.assert_('<table><head><row><cell role="label">Firstly</cell>' in
            tei_table)
        self.assert_('<row><cell role="data">B.1</cell><cell role="data">B.2</cell></row>'
            in tei_table)

    def test_code(self):

        # code, inline and block
        self.assertEqual('<p>Here is some <code>code</code> inline.</p>',
            markdown_tei.convert('Here is some `code` inline.'))
        code_snippet = '''require 'redcarpet'
markdown = Redcarpet.new("Hello World!")
puts markdown.to_html'''
        self.assertEqual('<code lang="ruby">%s</code>' % code_snippet,
            markdown_tei.convert('```ruby\n%s\n```' % code_snippet))

    def test_audio(self):
        # using html5 audio embedded in markdown
        mimetype = 'audio/mpeg'
        url = 'http://some.audio/file.mp3'
        audio = '''<audio controls='controls'>
  <source src='%s' type='%s'/>
</audio>''' % (url, mimetype)

        self.assertEqual('<media mimeType="%s" url="%s"/>' % (mimetype, url),
            markdown_tei.convert(audio))

        # source attribute tag order shouldn't matter
        audio = '''<audio controls='controls'>
          <source type='%s' src='%s'/>
        </audio>''' % (mimetype, url)
        expected = '<media mimeType="%s" url="%s"/>' % (mimetype, url)
        self.assertEqual(expected, markdown_tei.convert(audio))

        audio_plus = '''<script>console.log("test");</script>

%s

testing  ... again ...''' % audio
        self.assert_(expected in markdown_tei.convert(audio_plus))

        # inline audio block
        audio_attrs = {
            'url': 'http://soundbible.com/mp3/Audience_Applause-Matthiew11-1206899159.mp3',
            'mimetype': 'audio/mpeg'
        }
        inline_audio = '''applause
text inline with audio<audio controls="controls">
<source src="%(url)s" type="%(mimetype)s"/>
</audio>will cause the TEI to break''' % audio_attrs
        inline_tei_audio = markdown_tei.convert(inline_audio)
        self.assert_('<media mimeType="%(mimetype)s" url="%(url)s"/>' % audio_attrs
             in inline_tei_audio)

        # no type attribute - mimetype inferred from audio src url
        mimetype = 'audio/mpeg'
        url = 'http://some.audio/file.mp3'
        audio = '''<audio controls='controls'>
          <source src='%s'/>
        </audio>''' % (url, )
        expected = '<media mimeType="%s" url="%s"/>' % (mimetype, url)
        self.assertEqual(expected, markdown_tei.convert(audio))

        mimetype = 'audio/aac'
        url = 'http://some.audio/file.aac'
        audio = '''<audio controls='controls'>
          <source src='%s'/>
        </audio>''' % (url, )
        expected = '<media mimeType="%s" url="%s"/>' % (mimetype, url)
        self.assertEqual(expected, markdown_tei.convert(audio))

        # fallback mimetype where extension is not informative
        mimetype = 'audio/mpeg'
        url = 'http://some.audio/file/without/ext/'
        audio = '''<audio controls='controls'>
          <source src='%s'/>
        </audio>''' % (url, )
        expected = '<media mimeType="%s" url="%s"/>' % (mimetype, url)
        self.assertEqual(expected, markdown_tei.convert(audio))




