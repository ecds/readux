# methods for generating annotated tei
from eulxml.xmlmap import load_xmlobject_from_string, teimap
from lxml import etree
import mistune
from readux.books.models import TeiZone, TeiNote


def annotated_tei(tei, annotations):
    # iterate throuth the annotations associated with this volume
    # and insert them into the tei based on the content they reference

    # perhaps some sanity-checking: compare annotation total vs
    # number actually added as we go page-by-page
    for note in annotations.all():
        ark = note.info()['ark']
        print note

    for page in tei.page_list:
        print 'tei page %s' % page.id
        page_annotations = annotations.filter(extra_data__contains=page.id)
        print page_annotations
        if page_annotations.exists():
            print 'page annotations'
            for note in page_annotations:
                print note.id
                insert_note(page, note)


    return tei


def annotation_to_tei(annotation):
    'Generate a tei note from an annotation'
    # needs to handle formatting, tags, etc

    # TODO: tags
    # should we include annotation created/edited dates?

    # sample note provided by Alice
    # <note resp="JPK" xml:id="oshnp50n1" n="1"><p>This is an example note.</p></note>

    # convert markdown-formatted text content to tei
    note_content = markdown_to_tei(annotation.text)
    # markdown results could be a list of paragraphs, and not a proper
    # xml tree; also, pags do not include namespace
    # wrap in a note element and set the default namespace as tei
    teinote = load_xmlobject_from_string('<note xmlns="%s">%s</note>' % \
        (teimap.TEI_NAMESPACE, note_content),
        TeiNote)

    # should we include full readux uri?
    # or is annotation uuid enough?
    teinote.id = annotation.get_absolute_url()

    # if the annotation has an associated user, mark the author
    # as responsible for the note
    if annotation.user:
        teinote.resp = annotation.user.username

    return teinote

def html_xpath_to_tei(xpath):
    # convert xpaths generated on the readux site to the
    # equivalent xpaths for the corresponding tei content
    return xpath.replace('div', 'tei:zone') \
                .replace('span', 'tei:w') \
                .replace('@id', '@xml:id')

def insert_note(teipage, annotation):

    info = annotation.info()
    # convert html xpaths to tei
    if info['ranges']:
        # NOTE: assuming single range selection for now
        # annotator model supports multiple, but UI does not currently
        # support it
        start_xpath = html_xpath_to_tei(info['ranges'][0]['start'])
        end_xpath = html_xpath_to_tei(info['ranges'][0]['end'])
        print 'xpaths - ', start_xpath, end_xpath
        start = teipage.node.xpath(start_xpath, namespaces=TeiZone.ROOT_NAMESPACES)
        end = teipage.node.xpath(end_xpath, namespaces=TeiZone.ROOT_NAMESPACES)
        print 'start node = ', start, ' end node = ', end
        # insert reference using start/end xpaths & offsets

    # if no ranges, then image annotation;
    # create a new surface/zone referencing the coordinates (?)


    # then call annotation_to_tei
    # and insert the resulting note in the appropriate part of the
    # document


    # {u'ranges': [
    #     {u'start': u'//div[@id="fnstr.idm291623100992"]/span[1]',
    #     u'end': u'//div[@id="fnstr.idm291623092160"]/span[1]',
    #     u'startOffset': 0,
    #     u'endOffset': 5}], u'permissions': {},
    #     u'ark': u'http://testpid.library.emory.edu/ark:/25593/ntdfb', u'tags': [u'test', u' text-annotation']}



def markdown_to_tei(text):
    'Render markdown text as simple TEI'
    # does not include namespace or wrapping elment
    mkdown = mistune.Markdown(renderer=TeiMarkdownRenderer())
    return mkdown(text)


class TeiMarkdownRenderer(mistune.Renderer):

    def __init__(self, **kwargs):
        self.options = kwargs

    # def placeholder(self):
    #     """Returns the default, empty output value for the renderer.
    #     All renderer methods use the '+=' operator to append to this value.
    #     Default is a string so rendering HTML can build up a result string with
    #     the rendered Markdown.
    #     Can be overridden by Renderer subclasses to be types like an empty
    #     list, allowing the renderer to create a tree-like structure to
    #     represent the document (which can then be reprocessed later into a
    #     separate format like docx or pdf).
    #     """
    #     return "<?xml:namespace ns='%s' ?>" % TeiNote.ROOT_NS

    def block_code(self, code, lang=None):
        """Rendering block level code. ``pre > code``.
        :param code: text content of the code block.
        :param lang: language of the given code.
        """
        # TODO
        # - is there any equivalent in tei?
        code = code.rstrip('\n')
        if not lang:
            code = mistune.escape(code, smart_amp=False)
            return '<pre><code>%s\n</code></pre>\n' % code
        code = mistune.escape(code, quote=True, smart_amp=False)
        return '<pre><code class="lang-%s">%s\n</code></pre>\n' % (lang, code)

    def block_quote(self, text):
        """Rendering <quote> with the given text.
        :param text: text content of the blockquote.
        """
        return '<quote>%s</quote>' % text.rstrip('\n')

    def block_html(self, html):
        """Rendering block level pure html content.
        :param html: text content of the html snippet.
        """
        # TODO
        if self.options.get('skip_style') and \
           html.lower().startswith('<style'):
            return ''
        if self.options.get('escape'):
            return mistune.escape(html)
        return html

    def header(self, text, level, raw=None):
        """Rendering header/heading tags like ``<h1>`` ``<h2>``.
        :param text: rendered text content for the header.
        :param level: a number for the header level, for example: 1.
        :param raw: raw text content of the header.
        """
        # TODO
        return '<h%d>%s</h%d>\n' % (level, text, level)

    def hrule(self):
        """Rendering method for ``<hr>`` tag."""
        # TODO
        if self.options.get('use_xhtml'):
            return '<hr />\n'
        return '<hr>\n'

    def list(self, body, ordered=True):
        """Rendering list tags.
        :param body: body contents of the list.
        :param ordered: whether this list is ordered or not.
        """
        attr = ''
        if ordered:
            attr = ' rend="numbered"'
        return '<list%s>%s</list>' % (attr, body)

    def list_item(self, text):
        """Rendering list item."""
        return '<item>%s</item>' % text

    def paragraph(self, text):
        """Rendering paragraph tags. Like ``<p>``."""
        return '<p>%s</p>' % text.strip(' ')

    def table(self, header, body):
        """Rendering table element. Wrap header and body in it.
        :param header: header part of the table.
        :param body: body part of the table.
        """
        # TODO
        return (
            '<table>\n<thead>%s</thead>\n'
            '<tbody>\n%s</tbody>\n</table>\n'
        ) % (header, body)

    def table_row(self, content):
        """Rendering a table row. Like ``<tr>``.
        :param content: content of current table row.
        """
        # TODO
        return '<tr>\n%s</tr>\n' % content

    def table_cell(self, content, **flags):
        """Rendering a table cell. Like ``<th>`` ``<td>``.
        :param content: content of current table cell.
        :param header: whether this is header or not.
        :param align: align of current table cell.
        """
        # TODO
        if flags['header']:
            tag = 'th'
        else:
            tag = 'td'
        align = flags['align']
        if not align:
            return '<%s>%s</%s>\n' % (tag, content, tag)
        return '<%s style="text-align:%s">%s</%s>\n' % (
            tag, align, content, tag
        )

    def double_emphasis(self, text):
        """Rendering **strong** text.
        :param text: text content for emphasis.
        """
        return '<emph rend="bold">%s</emph>' % text

    def emphasis(self, text):
        """Rendering *emphasis* text.
        :param text: text content for emphasis.
        """
        return '<emph rend="italic">%s</emph>' % text

    def codespan(self, text):
        """Rendering inline `code` text.
        :param text: text content for inline code.
        """
        # TODO
        text = mistune.escape(text.rstrip(), smart_amp=False)
        return '<code>%s</code>' % text

    def linebreak(self):
        """Rendering line break like ``<br>``."""
        # TODO
        if self.options.get('use_xhtml'):
            return '<br />\n'
        return '<br>\n'

    def strikethrough(self, text):
        """Rendering ~~strikethrough~~ text.
        :param text: text content for strikethrough.
        """
        return '<del>%s</del>' % text

    def text(self, text):
        """Rendering unformatted text.
        :param text: text content.
        """
        # TODO
        return mistune.escape(text)

    def autolink(self, link, is_email=False):
        """Rendering a given link or email address.
        :param link: link content or email address.
        :param is_email: whether this is an email or not.
        """
        link = mistune.escape(link)
        if is_email:
            tag = 'email'
            attr = ''
        else:
            tag = 'link'
            attr = ' target="%s"' % link
        return '<%(tag)s%(attr)>%(text)s</%(tag)s>' % {
            'tag':tag, 'text': link, 'attr': attr}

    def link(self, link, title, text):
        """Rendering a given link with content and title.
        :param link: href link for ``<a>`` tag.
        :param title: title content for `title` attribute.
        :param text: text content for description.
        """
        # TODO
        if link.startswith('javascript:'):
            link = ''
        if not title:
            return '<a href="%s">%s</a>' % (link, text)
        title = mistune.escape(title, quote=True)
        return '<a href="%s" title="%s">%s</a>' % (link, title, text)

    def image(self, src, title, text):
        """Rendering a image with title and text.
        :param src: source link of the image.
        :param title: title text of the image.
        :param text: alt text of the image.
        """
        if src.startswith('javascript:'):
            src = ''
        text = mistune.escape(text, quote=True)
        # markdown doesn't necessarily include mimetype;
        # is this required in tei?
        # attempt to infer from image url
        mimetype = 'image/%s' % (src.rsplit('.', 1)[-1])
        tag = '<media mimetype="%s" url="%s">' % (mimetype, src)
        if title or text:
            desc_parts = ['<desc>']
            if title:
                desc_parts.append('<head>%s</head>' % title)
            if text:
                desc_parts.append('<p>%s</p>' % text)
            desc_parts.append('</desc>')
            tag += ''.join(desc_parts)
        tag += '</media>'
        return tag


    def inline_html(self, html):
        """Rendering span level pure html content.
        :param html: text content of the html snippet.
        """
        # TODO
        if self.options.get('escape'):
            return mistune.escape(html)
        return html

    def newline(self):
        """Rendering newline element."""
        # TODO
        return ''

    def footnote_ref(self, key, index):
        """Rendering the ref anchor of a footnote.
        :param key: identity key for the footnote.
        :param index: the index count of current footnote.
        """
        return '<ref target="#fn%s" type="noteAnchor">%s</ref>' % \
            (key, index)

    def footnote_item(self, key, text):
        """Rendering a footnote item.
        :param key: identity key for the footnote.
        :param text: text content of the footnote.
        """
        return '<note xml:id="fn%s" type="footnote">%s</note>' % (key, text)

    def footnotes(self, text):
        """Wrapper for all footnotes.
        :param text: contents of all footnotes.
        """
        return '<div type="footnotes">%s</div>' % text


