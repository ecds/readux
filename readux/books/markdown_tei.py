import re
import mistune

def convert(text):
    '''Render markdown text as simple TEI.
    Does not include namespaces or wrapping elements; assumes that the
    rendered markdown will be inserted into a TEI document as text
    content, and that it is not intended to be an entire, valid document
    on its own.
    '''
    mkdown = mistune.Markdown(renderer=TeiMarkdownRenderer())
    return mkdown(text)


class TeiMarkdownRenderer(mistune.Renderer):
    '''TEI Markdown renderer for use with :mod:`mistune` markdown
    parsing and rendering library.  Renderer is based on the built-in
    mistune HTML renderer.'''

    audio_regex = re.compile(
        r'<audio[^>]*>\s*'   # open audio tag, with any attributes
        # source with url and type in any order
        r'<source\s+(src|type)=["\']([^"\']+)["\']\s+(src|type)=["\']([^"\']+)["\']\s+/>'
        r'\s*</audio>',      # close audio tag
        re.MULTILINE | re.DOTALL | re.UNICODE
    )

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
        """Rendering block level code.

        :param code: text content of the code block.
        :param lang: language of the given code.
        """
        code = code.rstrip('\n')
        attr = ''
        if lang:
            attr = ' lang="%s"' % lang
        return '<code%s>%s</code>' % (attr, code)

    def block_quote(self, text):
        """Rendering <quote> with the given text.

        :param text: text content of the blockquote.
        """
        return '<quote>%s</quote>' % text.rstrip('\n')

    def block_html(self, html):
        """Rendering block level pure html content.
        Currently only supports html5 audio tags.

        :param html: text content of the html snippet.
        """
        match = self.audio_regex.match(html)
        if match:
            # returns list of tuples; first of each pair is the attribute name
            values = match.groups()
            values_dict = {
                values[0]: values[1],
                values[2]: values[3]
            }
            return '<media mimeType="%(type)s" url="%(src)s"/>' % values_dict

        # NOTE: default mistune logic here; probably not useful for TEI
        if self.options.get('skip_style') and \
           html.lower().startswith('<style'):
            return ''
        if self.options.get('escape'):
            return mistune.escape(html)
        return html

    def header(self, text, level, raw=None):
        """Rendering header/heading.

        :param text: rendered text content for the header.
        :param level: a number for the header level, for example: 1.
        :param raw: raw text content of the header.
        """
        return '<head type="level%d">%s</head>' % (level, text)

    def hrule(self):
        """Rendering method for horizontal rule."""
        return '<milestone @rend="horizontal-rule"/>'

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
        return (
            '<table><head>%s</head>'
            '%s</table>'
        ) % (header, body)

    def table_row(self, content):
        """Rendering a table row.

        :param content: content of current table row.
        """
        return '<row>%s</row>' % content

    def table_cell(self, content, **flags):
        """Rendering a table cell.

        :param content: content of current table cell.
        :param header: whether this is header or not.
        :param align: align of current table cell.
        """
        if flags['header']:
            role = "label"
        else:
            role = "data"
        additional_attrs = ''
        if 'align' in flags and flags['align']:
            additional_attrs = ' rend="%s"' % flags['align']
        return '<cell role="%s"%s>%s</cell>' % (role, additional_attrs, content)

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
        text = mistune.escape(text.rstrip(), smart_amp=False)
        return '<code>%s</code>' % text

    def linebreak(self):
        """Rendering line break."""
        return '<lb/>'

    def strikethrough(self, text):
        """Rendering ~~strikethrough~~ text.

        :param text: text content for strikethrough.
        """
        return '<del>%s</del>' % text

    def text(self, text):
        """Rendering unformatted text.

        :param text: text content.
        """
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
            tag = 'ref'
            attr = ' target="%s"' % link
        return '<%(tag)s%(attr)>%(text)s</%(tag)s>' % {
            'tag':tag, 'text': link, 'attr': attr}

    def link(self, link, title, text):
        """Rendering a given link with content and title.

        :param link: href link for ``<a>`` tag.
        :param title: title content for `title` attribute.
        :param text: text content for description.
        """
        if link.startswith('javascript:'):
            link = ''
        attr = ''
        if title:
            attr = ' n="%s"' % mistune.escape(title, quote=True)

        return '<ref target="%s"%s>%s</ref>' % (link, attr, text)

    def image(self, src, title, text):
        """Rendering a image with title and text.

        :param src: source link of the image.
        :param title: title text of the image.
        :param text: alt text of the image.
        """
        if src.startswith('javascript:'):
            src = ''
        text = mistune.escape(text, quote=True)
        # markdown doesn't include mimetype, but it's required in TEI
        # infer mimetype based on image suffix in the url
        image_suffix = (src.rsplit('.', 1)[-1])
        mimetype = "image/*"
        if image_suffix in ['gif', 'png', 'jpeg']:
            mimetype = 'image/%s' % image_suffix
        elif image_suffix == 'jpg':
            mimetype = 'image/jpeg'
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


