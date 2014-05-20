'''
:class:`eulxml.xmlmap.XmlObject` classes for working with ABBYY
FineReadux OCR XML.

Currently supports **FineReader6-schema-v1** and
**FineReader8-schema-v2**.

----
'''
from eulxml import xmlmap

class Base(xmlmap.XmlObject):
    '''Base :class:`eulxml.xmlmap.XmlObject` for ABBYY OCR XML with
    common namespace declarations.
    
    '''
    ROOT_NAMESPACES = {
        'fr6v1': 'http://www.abbyy.com/FineReader_xml/FineReader6-schema-v1.xml',
        'fr8v2': 'http://www.abbyy.com/FineReader_xml/FineReader8-schema-v2.xml'
    }
    'namespaces for supported versions of FineReader xml'

def frns(xpath):
    '''Utility function to convert a simple xpath to match any of the
    configured versions of ABBYY FineReader XML namespaces. Example
    conversions:
    * ``page`` becomes ``f1:page|f2:page``
    * ``text/par`` becomes ``f1:page/f1:text|f2:page/f2:text``

    Uses all declared namespace prefixes from
    :attr:`Base.ROOT_NAMESPACES`
    '''
    namespaces = Base.ROOT_NAMESPACES.keys()
    return '|'.join('/'.join('%s:%s' % (ns, el) for el in xpath.split('/'))
                    for ns in namespaces)
    
class Formatting(Base):
    '''A group of characters in a single :class:`Line` with uniform
    formatting.'''
    ROOT_NAME = 'formatting'
    language = xmlmap.StringField('@lang')
    'language of this formatted section'
    text = xmlmap.StringField('text()')
    'text value'
    # char params ?
    # boolean attributes for: ff, fs, bold, italic, subscript, superscript,
    # smallcaps, underline, strikeout, color, scaling, spacing

class Line(Base):
    '''A single line of text in a :class:`Paragraph`.'''
    ROOT_NAME = 'line'
    baseline = xmlmap.IntegerField('@baseline')
    'integer baseline'
    left = xmlmap.IntegerField('@l')
    'integer left'
    top = xmlmap.IntegerField('@t')
    'integer top'
    right = xmlmap.IntegerField('@r')
    'integer right'
    bottom = xmlmap.IntegerField('@b')
    'integer bottom'
    formatted_text = xmlmap.NodeListField(frns('formatting'),
                                          Formatting)
    'list of :class:`Formatting` elements'

class Paragraph(Base):
    '''A single paragraph of text somewhere in a :class:`Document`.'''
    ROOT_NAME = 'par'
    align = xmlmap.StringField('@align') # default is Left; Center, Right, Justified
    'text alignment (Left, Center, Right, Justified)'
    left_indent = xmlmap.IntegerField('@leftIndent')
    'integer left indent'
    right_indent = xmlmap.IntegerField('@rightIndent')
    'integer right indent'
    start_indent = xmlmap.IntegerField('@startIndent')
    'integer start indent'
    line_spacing = xmlmap.IntegerField('@lineSpacing')
    'integer line spacing'
    # dropChars stuff ?
    lines = xmlmap.NodeListField(frns('line'), Line)
    'list of :class:`Line` elements'
    
class Block(Base):
    ROOT_NAME = 'page'
    '''A single block of content on a :class:`Page`.'''
    type = xmlmap.StringField('@blockType') # Text, Table, Picture, Barcode
    'type of block (Text, Table, Picture, Barcode)'
    left = xmlmap.IntegerField('@l')
    'integer left'
    top = xmlmap.IntegerField('@t')
    'integer top'
    right = xmlmap.IntegerField('@r')
    'integer right'
    bottom = xmlmap.IntegerField('@b')
    'integer bottom'
    # must have one & only one region;
    # region/rect dimensions appears to be redundant...
    paragraphs = xmlmap.NodeListField(frns('text/par'), Paragraph)
    'list of :class:`Paragraph` elements'

class Page(Base):
    '''A single page of a :class:`Document`.'''
    ROOT_NAME = 'page'
    width = xmlmap.IntegerField('@width')
    'integer width'
    height = xmlmap.IntegerField('@height')
    'integer height'
    resolution = xmlmap.IntegerField('@resolution')
    'integer resolution'
    blocks = xmlmap.NodeListField(frns('block'), Block)
    'list of :class:`Block` elements in this page'
    text_blocks = xmlmap.NodeListField(frns('block[@blockType="Text"]'),
                                       Block)
    'text :class:`Block` elements (where type is "Text")'
    picture_blocks = xmlmap.NodeListField(frns('block[@blockType="Picture"]'),
                                          Block)
    'picture :class:`Block` elements (where type is "Picture")'
    # block position info possibly redundant? map paragraphs directly
    paragraphs = xmlmap.NodeListField(frns('block/text/par'),
                                      Paragraph)
    'list of :class:`Paragraph` elements in any of the blocks on this page'

class Document(Base):
    ''':class:`~eulxml.xmlmap.XmlObject` class for an ABBYY
    OCR XML Document.

    .. Note::
      Currently there is no support for tabular formatting elements.
    '''
    ROOT_NAME ='document'
    pages = xmlmap.NodeListField(frns('page'), Page)
    'pages as :class:`Page`'
    page_count = xmlmap.IntegerField('@pagesCount')
    'integer page_count (document ``@pagesCount``)'
    language = xmlmap.StringField('@mainLanguage')
    'main language of the document'
    languages = xmlmap.StringField('@languages')
    'all languages included in the document'


