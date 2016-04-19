from django.conf import settings
from eulxml import xmlmap
from eulxml.xmlmap import teimap
from lxml import etree
import os

'''
:class:`eulxml.xmlmap.XmlObject` subclasses for dealing with TEI,
particularly for the TEI facsimile used for positional OCR data for
readux pages and for generating annotated TEI for export.
'''


class TeiBase(teimap.Tei):
    'Base class for all TEI objects, with all namespaces'
    ROOT_NS = teimap.TEI_NAMESPACE
    ROOT_NAMESPACES = {
        'tei' : ROOT_NS,
        'xml': 'http://www.w3.org/XML/1998/namespace',
        'xlink': 'http://www.w3.org/TR/xlink/',
    }

class Graphic(TeiBase):
    'TEI Graphic'
    ROOT_NAME = 'graphic'
    #: url
    url = xmlmap.StringField('@url')
    #: rend
    rend = xmlmap.StringField('@rend')

class Zone(TeiBase):
    'XmlObject for a zone in a TEI facsimile document'
    ROOT_NAME = 'zone'
    #: xml id
    id = xmlmap.StringField('@xml:id')
    #: n attribute
    n = xmlmap.StringField('@n')
    #: type attribute
    type = xmlmap.StringField('@type')
    #: upper left x coord
    ulx = xmlmap.FloatField('@ulx')
    #: upper left y coord
    uly = xmlmap.FloatField('@uly')
    #: lower right x coord
    lrx = xmlmap.FloatField('@lrx')
    #: lower right y coord
    lry = xmlmap.FloatField('@lry')
    #: xlink href
    href = xmlmap.StringField('@xlink:href')
    #: text content
    text = xmlmap.StringField('tei:line|tei:w')
    #: list of word zones contained in this zone (e.g., within a textLine zone)
    word_zones = xmlmap.NodeListField('.//tei:zone[@type="string"]', 'self')
    #: nearest preceding sibling word zone (e.g., previous word in this line), if any)
    preceding = xmlmap.NodeField('preceding-sibling::tei:zone[1]', 'self')
    #: nearest ancestor zone
    parent = xmlmap.NodeField('ancestor::tei:zone[1]', 'self')
    #: containing page
    page = xmlmap.NodeField('ancestor::tei:surface[@type="page"]', 'self')
    # not exactly a zone, but same attributes we care about (type, id, ulx/y, lrx/y)

    #: list of graphic elements (i.e. page images)
    graphics = xmlmap.NodeListField('tei:graphic', Graphic)

    # convenience mappings to specific sizes of page image
    #: full size image (tei:graphic with type "full")
    full_image = xmlmap.NodeField('tei:graphic[@type="full"]', Graphic)
    #: page size image (tei:graphic with type "page")
    page_image = xmlmap.NodeField('tei:graphic[@type="page"]', Graphic)
    #: thumbnail image (tei:graphic with type "thumbnail")
    thumbnail = xmlmap.NodeField('tei:graphic[@type="thumbnail"]', Graphic)
    #: small thumbnail image (tei:graphic with type "small-thumbnail")
    small_thumbnail = xmlmap.NodeField('tei:graphic[@type="small-thumbnail"]', Graphic)
    #: image info as provided by IIIF (tei:graphic with type "info")
    image_info = xmlmap.NodeField('tei:graphic[@type="info"]', Graphic)

    @property
    def width(self):
        'zone width'
        return self.lrx - self.ulx

    @property
    def height(self):
        'zone height'
        return self.lry - self.uly

    @property
    def avg_height(self):
        '''Calculated average height of word zones in the current zone
        (i.e. in a text line)'''
        if self.word_zones:
            word_heights = [w.height for w in self.word_zones]
            return sum(word_heights) / float(len(word_heights))

class Ref(TeiBase):
    'Tei reference'
    ROOT_NAME = 'ref'
    #: target
    target = xmlmap.StringField('@target')
    #: type
    type = xmlmap.StringField('@type')
    #: text
    text = xmlmap.StringField('text()')


class BiblStruct(TeiBase):
    'Structured Bibliographic citation'
    # minimal mappings for now
    ROOT_NAME = 'BiblStruct'
    #: xml id
    id = xmlmap.StringField('@xml:id')
    #: corresp
    corresp = xmlmap.StringField('@corresp')
    #: type
    type = xmlmap.StringField('@type')

class AnnotationWorksCited(TeiBase):
    milestone = xmlmap.NodeField('preceding-sibling::tei:milestone',
                                 xmlmap.XmlObject)
    ref_list = xmlmap.NodeField(
        'parent::tei:list[contains(tei:item/tei:anchor/@xml:id, "zotero")]',
        xmlmap.XmlObject)

class Note(TeiBase):
    'Tei Note, used here to contain an annotation'
    ROOT_NAME = 'note'
    #: xml id
    id = xmlmap.StringField('@xml:id')
    #: responsibility
    resp = xmlmap.StringField('@resp')
    #: target
    target = xmlmap.StringField('@target')
    #: type
    type = xmlmap.StringField('@type')
    #: ana attribute, e.g. for tag identifiers
    ana = xmlmap.StringField('@ana')
    #: xlink href
    href = xmlmap.StringField('@xlink:href')
    #: list of paragraphs as strings
    paragraphs = xmlmap.StringListField('tei:p')
    #: code for the markdown used in the original annotation
    markdown = xmlmap.StringField('tei:code[@lang="markdown"]')
    #: links to related pages
    related_pages = xmlmap.NodeListField('tei:ref[@type="related page"]',
        Ref)
    #: list of bibliographic citations/works cited
    citations = xmlmap.NodeListField('tei:listBibl/tei:biblStruct', BiblStruct)

    # in-text citation generated from markdown; these fields
    # are mapped so they can be removed from the annotated tei document
    works_cited = xmlmap.NodeField(
        'tei:head[text() = "Works Cited"]',
        xmlmap.XmlObject)
    zotero_items = xmlmap.NodeField(
        'tei:list[contains(tei:item/tei:anchor/@xml:id, "zotero")]',
        xmlmap.XmlObject)
    works_cited_milestone = xmlmap.NodeField(
        'tei:milestone[following-sibling::tei:head/text() = "Works Cited"]',
        xmlmap.XmlObject)
    # mapped to remove empty list bibl element
    list_bibl = xmlmap.NodeField('tei:listBibl', xmlmap.XmlObject)


class Bibl(TeiBase):
    'TEI Bibl, with mappings for digital edition and pdf urls'
    #: type
    type = xmlmap.StringField('@type')
    #: title
    title = xmlmap.StringField('tei:title')
    #: author
    authors = xmlmap.StringListField('tei:author')
    #: date
    date = xmlmap.StringField('tei:date')
    #: url to digital edition
    url = xmlmap.StringField('tei:ref[@type="digital-edition"]/@target')
    #: url to pdf of digital edition
    pdf_url = xmlmap.StringField('tei:ref[@type="pdf"]/@target')


class PublicationStatement(TeiBase):
    'Publication statement, with mapping for readux distributor'
    #: descriptive statement (paragraph)
    desc = xmlmap.StringField('tei:p')
    #: date in human-readable display format
    date = xmlmap.DateField('tei:date', '%B %d, %Y')
    #: normalized date
    date_normal = xmlmap.DateField('tei:date/@when', '%Y-%m-%d')
    #: readux distributor reference (includes ref with target of readux.library.emory.edu)
    distributor_readux = xmlmap.StringField('tei:distributor[@xml:id="readux"]/tei:ref[@target="http://readux.library.emory.edu"]')


class Facsimile(TeiBase):
    '''Extension of :class:`eulxml.xmlmap.teimap.TEI` to provide access
    to TEI facsimile elements'''
    #: local xsd schema
    XSD_SCHEMA = 'file://%s' % os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                           'schema', 'TEIPageView.xsd')
    # NOTE: using absolute path for schema to avoid path issues when
    # building documentation on readthedocs.org

    ROOT_NAME = 'TEI'
    xmlschema = etree.XMLSchema(etree.parse(XSD_SCHEMA))
    # NOTE: not using xmlmap.loadSchema because it doesn't correctly load
    # referenced files in the same directory

    #: surface with type page, as :class:`Zone`
    page = xmlmap.NodeField('tei:facsimile/tei:surface[@type="page"]', Zone)
    #: list of pages (surface with type page)
    page_list = xmlmap.NodeListField('tei:facsimile/tei:surface[@type="page"]', Zone)
    # NOTE: tei facsimile could include illustrations, but ignoring those for now

    #: list of zones with type textLine or line as :class:`Zone`
    lines = xmlmap.NodeListField('tei:facsimile//tei:zone[@type="textLine" or @type="line"]', Zone)
    #: list of word zones (type string) as :class:`Zone`
    word_zones = xmlmap.NodeListField('tei:facsimile//tei:zone[@type="string"]', Zone)

    #: publication statment distributor
    distributor = xmlmap.StringField('tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:distributor')
    #: publication statmnt as :class:`PublicationStatement`
    pubstmt = xmlmap.NodeField('tei:teiHeader/tei:fileDesc/tei:publicationStmt',
        PublicationStatement)

    #: source description for the original volume
    original_source = xmlmap.NodeField('tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:bibl[@type="original"]',
        Bibl)
    #: source description for the readux digital edition
    digital_source = xmlmap.NodeField('tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:bibl[@type="digital"]',
        Bibl)


class Name(TeiBase):
    'Tei NAME, with id attribute and value'
    ROOT_NAME = 'name'
    #: xml id
    id = xmlmap.StringField('@xml:id')
    #: full name
    value = xmlmap.StringField('.')


class AnnotatedFacsimile(Facsimile):
    '''Annotated Tei facsimile, with mappings needed to generate
    TEI with annotations.
    '''
    #: main tei title
    main_title = xmlmap.StringField('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[@type="full"]/tei:title[@type="main"]')
    #: tei subtitle (e.g., annotated edition)
    subtitle = xmlmap.StringField('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title[@type="full"]/tei:title[@type="sub"]')

    #: responsibility statement text
    responsibility = xmlmap.StringField('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:respStmt/tei:resp')
    #: responsibility statement names
    responsible_names = xmlmap.NodeListField('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:respStmt/tei:name',
        Name)

    # additional mappings for annotation data

    #: list of annotations at body/div[@type="annotations"]/note[@type="annotation"], as :class:`Note`
    annotations = xmlmap.NodeListField('tei:body/tei:div[@type="annotations"]/tei:note[@type="annotation"]',
        Note)

    #: list of bibliographic citations/works cited
    citations = xmlmap.NodeListField('tei:listBibl/tei:biblStruct', BiblStruct)
    #: list of bibliographic citation ids

    citation_ids = xmlmap.StringListField('tei:listBibl/tei:biblStruct/@xml:id')

    #: annotation tags, as :class:`~eulxml.xmlmap.teimap.TeiInterpGroup`
    tags = xmlmap.NodeField('tei:back/tei:interpGrp[@type="tags"]',
        teimap.TeiInterpGroup)


    def page_id_by_xlink(self, link):
        results = self.node.xpath('//tei:surface[@type="page"][@xlink:href="%s"]/@xml:id' \
            % link, namespaces=self.ROOT_NAMESPACES)
        if results:
            return results[0]

class Anchor(TeiBase):
    'TEI Anchor, for marking start and end of text annotation highlights'
    ROOT_NAME = 'anchor'
    #: xml id
    id = xmlmap.StringField('@xml:id')
    #: type
    type = xmlmap.StringField('@type')
    #: next attribute
    next = xmlmap.StringField('@next')


class Interp(TeiBase, teimap.TeiInterp):
    # extend eulxml.xmlmap.teimap version because it does not include
    # the xml namespace for setting xml:id
    ROOT_NAME = 'interp'

