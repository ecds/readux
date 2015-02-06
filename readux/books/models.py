from UserDict import UserDict
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import permalink
from django.template.defaultfilters import truncatechars
from lxml.etree import XMLSyntaxError
import json
import logging
import os
from urllib import urlencode, unquote

from bs4 import BeautifulSoup
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, Namespace

from eulfedora.models import  Relation, ReverseRelation, \
    FileDatastream, XmlDatastream, DatastreamObject
from eulfedora.rdfns import relsext
from eulxml import xmlmap

from readux.books import abbyyocr
from readux.fedora import DigitalObject
from readux.collection.models import Collection
from readux.utils import solr_interface, absolutize_url


logger = logging.getLogger(__name__)


BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
DC = rdflib.Namespace('http://purl.org/dc/terms/')

REPOMGMT = Namespace(rdflib.URIRef('http://pid.emory.edu/ns/2011/repo-management/#'))
# local repo-management namespace also in use in the Keep
repomgmt_ns = {'eul-repomgmt': REPOMGMT}


class MinMarcxml(xmlmap.XmlObject):
    # minimal marc xml with only fields needed for readux import/display
    ROOT_NS = 'http://www.loc.gov/MARC21/slim'
    ROOT_NAMESPACES = { 'marc21' : ROOT_NS }

    ocm_number = xmlmap.StringField('marc21:record/marc21:controlfield[@tag="001"]')


class Book(DigitalObject):
    '''Fedora Book Object.  Extends :class:`~eulfedora.models.DigitalObject`.

    .. Note::

        This is a bare-minimum model, only implemented enough to support
        indexing and access to volumes.
    '''
    #: content model for books
    BOOK_CONTENT_MODEL = 'info:fedora/emory-control:ScannedBook-1.0'
    CONTENT_MODELS = [ BOOK_CONTENT_MODEL ]

    #: marcxml :class:`~eulfedora.models.XMlDatastream` with the metadata
    #: record for all associated volumes
    #: NOTE: using generic xmlobject for now
    marcxml = XmlDatastream("MARCXML", "MARC21 metadata", MinMarcxml, defaults={
        'control_group': 'M',
        'versionable': True,
    })

    #: :class:`~readux.collection.models.Collection` this book belongs to
    collection = Relation(relsext.isMemberOfCollection, type=Collection)

    #: default view for new object
    #: FIXME: needs at least preliminary book view to point to (?)
    NEW_OBJECT_VIEW = 'books:volume'

    @property
    def best_description(self):
        '''Single best description to use when only one can be displayed (e.g.,
        for twitter or facebook integration)
        '''
        # for now, just return the longest description
        # eventually we should be able to update this to make use of the MARCXML
        descriptions = list(self.dc.content.description_list)
        if descriptions:
            return sorted(descriptions, key=len, reverse=True)[0]

    @staticmethod
    def pids_by_label(label):
        '''Search Books by label and return a list of matching pids.'''
        solr = solr_interface()
        q = solr.query(content_model=Book.BOOK_CONTENT_MODEL,
                       label=label).field_limit('pid')
        return [result['pid'] for result in q]


# NOTE: Image and Page defined before Volume to allow referencing in
# Volume relation definitions


class Image(DigitalObject):
    ''':class:`~eulfedora.models.DigitalObject` for image content,
    with an Image-1.0 content model and Fedora services for image
    preview and manipulation.'''

    IMAGE_CONTENT_MODEL = 'info:fedora/emory-control:Image-1.0'
    CONTENT_MODELS = [ IMAGE_CONTENT_MODEL]
    IMAGE_SERVICE = 'emory-control:DjatokaImageService'

    content_types = ('image/jpeg', 'image/jp2', 'image/gif', 'image/bmp',
                     'image/png', 'image/tiff')
    'supported content types (mimetypes) for image datastream'

    image = FileDatastream("source-image", "Master image", defaults={
            'mimetype': 'image/tiff',
            # FIXME: versioned? checksum?
        })
    ':class:`~eulfedora.models.FileDatastream` with image content'

    def get_preview_image(self):
        'Return a version of the image suitable for preview or thumbnail'
        content, uri = self.getDissemination(self.IMAGE_SERVICE, 'getRegion',
                                             params={'level': 1})
        return content

    def get_region(self, **params):
        '''Call the getRegion method on the image service disseminator
        with any parameters the service supports, and return the
        results.'''
        return self.getDissemination(self.IMAGE_SERVICE, 'getRegion', params=params)

    def get_region_chunks(self, **params):
        # return getRegion chunks as a generator for use with http response
        response = self.getDissemination(self.IMAGE_SERVICE, 'getRegion', params=params,
                                         return_http_response=True)
        # FIXME: check response code first?
        while True:
            chunk = response.read(4096)
            if not chunk:
                return
            yield chunk

    _image_metadata = None
    @property
    def image_metadata(self):
        '''Image metadata as returned by Djatoka getMetadata method
        (width, height, etc.).'''
        if self._image_metadata is None:
            imgmeta = self.getDissemination(self.IMAGE_SERVICE, 'getMetadata')
            # getDissemination returns a tuple of result, url
            # load the image metadata returned by djatoka via json and return
            # NOTE: this is eulfedora + requests syntax; old syntax was imgmeta[0]
            self._image_metadata = json.loads(imgmeta.content)
        return self._image_metadata

    # expose width & height from image metadata as properties
    @property
    def width(self):
        '''Width of :attr:`image` datastream, according to
        :attr:`image_metadata`.'''
        return int(self.image_metadata['width'])

    @property
    def height(self):
        '''Height of :attr:`image` datastream, according to
        :attr:`image_metadata`.'''
        return int(self.image_metadata['height'])


class Page(Image):
    '''Page object with common functionality for all versions of
    ScannedPage content.'''
    NEW_OBJECT_VIEW = 'books:page'
    #: pattern for retrieving page variants 1.0 or 1.1 from solr
    PAGE_CMODEL_PATTERN = 'info:fedora/emory-control:ScannedPage-1.?'

    page_order = Relation(REPOMGMT.pageOrder,
                          ns_prefix=repomgmt_ns, rdf_type=rdflib.XSD.int)

    volume = Relation(relsext.isConstituentOf, type=DigitalObject)
    'Volume this page is a part of, via `isConstituentOf` relation'
    # NOTE: can't set type as Volume here because it is not yet defined

    @permalink
    def get_absolute_url(self):
        'Absolute url to view this object within the site'
        return (self.NEW_OBJECT_VIEW, [str(self.pid)])

    @property
    def display_label(self):
        '''Display label, for use in html titles, twitter/facebook metadata, etc.'''
        return '%s, p. %d' % (self.volume.display_label, self.page_order)

    def get_fulltext(self):
        # to be implemented by version-specific subclass
        pass

    def has_fulltext(self):
        # to be implemented by version-specific subclass
        pass

    def index_data(self):
        '''Extend the default :meth:`eulfedora.models.DigitalObject.index_data`
        method to include fields needed for Page objects.'''
        data = super(Page, self).index_data()
        if self.page_order is not None:
            data['page_order'] = self.page_order

        # if OCR text is available, index it as page fulltext, for searching & highlighting
        if self.has_fulltext():
            data['page_text'] = self.get_fulltext()

        return data

    @property
    def has_requisite_content_models(self):
        ''':type: bool

        True when the current object has the expected content models
        for one of the supported Page variants.'''
        # extending default implementation because pade object should include
        # image cmodel and either page 1.0 or page 1.1
        return (self.has_model(Image.IMAGE_CONTENT_MODEL) & \
               (self.has_model(PageV1_0.PAGE_CONTENT_MODEL) | \
               self.has_model(PageV1_1.PAGE_CONTENT_MODEL)))


class PageV1_0(Page):
    '''Page subclass for emory-control:ScannedPage-1.0.'''
    # NOTE: eulfedora syncrepo only knows how to create content models for
    # DigitalObject classes with only one content model, so a fixture
    # cmodel object is provided in fixtures/initial_data
    PAGE_CONTENT_MODEL = 'info:fedora/emory-control:ScannedPage-1.0'
    CONTENT_MODELS = [PAGE_CONTENT_MODEL, Image.IMAGE_CONTENT_MODEL]
    NEW_OBJECT_VIEW = 'books:page'

    text = FileDatastream('text', "page text", defaults={
            'mimetype': 'text/plain',
        })
    ''':class:`~eulfedora.models.FileDatastream` page text content
    generated by OCR'''

    position = FileDatastream('position', "word positions", defaults={
            'mimetype': 'text/plain',
        })
    ''':class:`~eulfedora.models.FileDatastream` word position
    information generated by OCR'''

    def has_fulltext(self):
        return self.text.exists

    def get_fulltext(self):
        '''Sanitized OCR full-text, e.g., for indexing or text analysis'''

        if self.text.exists:
            # if content is a StreamIO, use getvalue to avoid utf-8 issues
            if hasattr(self.text.content, 'getvalue'):
                textval =  self.text.content.getvalue().decode('utf-8', 'replace')
                # remove control characters
                control_chars = dict.fromkeys(range(32))
                # replace whitespace control characters with a space:
                #   tab, line feed, carriage return
                return textval.translate(control_chars)
            else:
                return self.text.content


class PageV1_1(Page):
    '''Page subclass for emory-control:ScannedPage-1.1.'''
    # NOTE: fixture cmodel provided in fixtures/initial_data
    PAGE_CONTENT_MODEL = 'info:fedora/emory-control:ScannedPage-1.1'
    CONTENT_MODELS = [PAGE_CONTENT_MODEL, Image.IMAGE_CONTENT_MODEL]
    NEW_OBJECT_VIEW = 'books:page'

    #: xml ocr datastream for mets/alto content for this page;
    #: keeping text datastream id for consistency with ScannedPage-1.0
    ocr = XmlDatastream('text', "OCR XML for page content", xmlmap.XmlObject, defaults={
        'control_group': 'M',
        'versionable': True,
    })

    def has_fulltext(self):
        return self.ocr.exists

    def get_fulltext(self):
        '''Sanitized OCR full-text, e.g., for indexing or text analysis'''
        # for simplicity and speed, use beautifulsoup to pull text content from the
        # alto ocr xml.
        # explicitly request generic ds object to avoid attempting to parse as xml
        ds = self.getDatastreamObject(self.ocr.id, dsobj_type=DatastreamObject)
        xmlsoup = BeautifulSoup(ds.content)

        # text content is grouped by line (TextLine element), and then contained
        # in the "CONTENT" attribute of String elements.
        return '\n'.join((' '.join(s['content'] for s in line.find_all('string')))
                         for line in xmlsoup.find_all('textline'))


class BaseVolume(object):
    '''Common functionality for :class:`Volume` and :class:`SolrVolume`'''

    # expects properties for pid, label, language

    @property
    def control_key(self):
        'Control key for this Book title (e.g., ocm02872816)'
        # LSDI Volume object label is ocm#_vol, e.g. ocn460678076_V.0
        ocm, sep, vol = self.label.partition('_')
        return ocm

    @property
    def volume(self):
        'volume label for this Book (e.g., v.1)'
        # LSDI Volume object label is ocm#_vol, e.g. ocn460678076_V.0
        ocm, sep, vol = self.label.partition('_')
        # if V.0, return no volume
        if vol.lower() == 'v.0':
            return ''
        return vol

    @property
    def noid(self):
        'short-form of pid'
        pidspace, sep, noid = self.pid.partition(':')
        return noid

    def fulltext_absolute_url(self):
        '''Generate an absolute url to the text view for this volume
        for use with external services such as voyant-tools.org'''
        return absolutize_url(reverse('books:text', kwargs={'pid': self.pid}))

    def voyant_url(self):
        '''Generate a url for sending the content of the current volume to Voyant
        for text analysis.'''

        url_params = {
            'corpus': self.pid,
            'archive': self.fulltext_absolute_url()
        }
            # if language is known to be english, set a default stopword list
        # NOTE: we could add this for other languages at some point
        if self.language and "eng" in self.language:
            url_params['stopList'] = 'stop.en.taporware.txt'

        return "http://voyant-tools.org/?%s" % urlencode(url_params)

    def pdf_url(self):
        '''Local PDF url, including starting page directive (#page=N) if start
        page is set.'''
        url = unquote(reverse('books:pdf', kwargs={'pid': self.pid}))
        if self.start_page:
            url = '%s#page=%d' % (url, self.start_page)
        return url

class Volume(DigitalObject, BaseVolume):
    '''Fedora Volume object with common functionality for all versions.
    Extends :class:`~eulfedora.models.DigitalObject` and :class:`BaseVolume`.'''

    #: content model pattern for finding supported variant volumes
    VOLUME_CMODEL_PATTERN = "info:fedora/emory-control:ScannedVolume-1.?"

    # inherits DC, RELS-EXT
    # related to parent Book object via isConstituentOf

    #: pdf :class:`~eulfedora.models.FileDatastream` with the content
    #: of the Volume (page images with OCR text behind)
    pdf = FileDatastream("PDF", "PDF datastream", defaults={
        'mimetype': 'application/pdf',
        'versionable': True,
    })

    #: :class:`Page` that is the primary image for this volume (e.g., cover image)
    primary_image = Relation(REPOMGMT.hasPrimaryImage, Page, repomgmt_ns)
    #: list of :class:`Page` for all the pages in this book, if available
    pages = ReverseRelation(relsext.isConstituentOf, Page, multiple=True)

    #: :class:`Book` this volume is associated with
    book = Relation(relsext.isConstituentOf, type=Book)

    #: start page - 1-based index of the first non-blank page in the PDF
    start_page = Relation(REPOMGMT.startPage,
                          ns_prefix=repomgmt_ns, rdf_type=rdflib.XSD.int)

    @property
    def has_requisite_content_models(self):
        ''':type: bool

        True when the current object has the expected content models
        for one of the supported Volume variants.'''
        # extending default implementation because volume object should include
        # either volume 1.0 or volume 1.1
        return self.has_model(VolumeV1_0.VOLUME_CONTENT_MODEL) | \
               self.has_model(VolumeV1_1.VOLUME_CONTENT_MODEL)


    @permalink
    def get_absolute_url(self):
        'Absolute url to view this object within the site'
        return ('books:volume', [str(self.pid)])

    # def get_pdf_url(self):
    #     return reverse('books:pdf', kwargs={'pid': self.pid})

    @property
    def page_count(self):
        'Number of pages associated with this volume, based on RELS-EXT isConstituentOf'
        if self.pages:
            return len(self.pages)

        # If no pages are ingested as self.pages is None, return 0
        return 0

    @property
    def has_pages(self):
        'boolean flag indicating if this volume has pages loaded'
        if self.pages:
            # pages exist and more than just the cover / primary image
            return len(self.pages) > 1
        else:
            return False

    @property
    def title(self):
        return self.dc.content.title.rstrip().rstrip('/')

    @property
    def display_label(self):
        '''Display label, for use in html titles, twitter/facebook metadata, etc.
        Truncates the title to the first 150 characters, and includes volume information
        if any.
        '''
        vol = ' [%s]' % self.volume if self.volume else ''
        return '%s%s' % (truncatechars(self.title.rstrip(), 150), vol)

    @property
    def title_part1(self):
        'Volume title, up to the first 150 characters'
        return self.title[:150]

    @property
    def title_part2(self):
        'Volume title after the first 150 characters'
        return self.title[150:].strip()

    @property
    def creator(self):
        return self.book.dc.content.creator_list

    @property
    def date(self):
        # some books (at least) include the digitization date (date of the
        # electronic ediction). If there are multiple dates, only include the oldest.

        # if dates are present in current volume dc, use those
        if self.dc.content.date_list:
            dates = self.dc.content.date_list
        # otherwise, use dates from book dc
        else:
            dates = self.book.dc.content.date_list

        if len(dates) > 1:
            date = sorted([d.strip('[]') for d in dates])[0]
            return [date]
        else:
            # convert eulxml list to normal list so it can be serialized via json
            return list(dates)

    def index_data(self):
        '''Extend the default
        :meth:`eulfedora.models.DigitalObject.index_data`
        method to include additional fields specific to Volumes.'''

        data = super(Volume, self).index_data()

        if self.fulltext_available:
            data['fulltext'] = self.get_fulltext()

        # pulling text content from the PDF is significantly slower;
        # - only pdf if ocr xml is not available or errored
        # NOTE: pdf to text seems to be hanging; disabling for now
        # if 'fulltext' not in data:
        #     data['fulltext'] = pdf_to_text(self.pdf.content)

        # index primary image pid to construct urls for cover image, first page
        if self.primary_image:
            data['hasPrimaryImage'] = self.primary_image.pid

        # index pdf start page so we can link to correct page from search results
        if self.start_page:
            data['start_page'] = self.start_page

        # index collection info
        data['collection_id'] = self.book.collection.pid
        data['collection_label'] = self.book.collection.short_label
        # book this volume is part of, for access to book-level metadata
        data['book_id'] = self.book.pid

        # add book-level metadata to text for keyword searching purposes
        # (preliminary; may want broken out for facets/fielded searching;
        # would be better to index on book object and use joins for that if possible...)

        # book_dc = self.book.dc.content

        # convert xmlmap lists to straight lists for json output
        data['creator'] = list(self.book.dc.content.creator_list)

        # some books (at least) include the digitization date (date of the
        # electronic ediction). Use local date property that returns only the oldest
        data['date'] = self.date

        if self.book.dc.content.subject_list:
            data['subject'] = list(self.book.dc.content.subject_list)

        # number of pages loaded for this book, to allow determining if page view is available
        data['page_count'] = self.page_count

        # size of the pdf
        if self.pdf and self.pdf.size:
            data['pdf_size'] = self.pdf.size

        return data

    #: supported unAPI formats, for use with :meth:`readux.books.views.unapi`
    unapi_formats = {
            'rdf_dc': {'type': 'application/rdf+xml', 'method': 'rdf_dc'}
    }

    @property
    def ark_uri(self):
        'fully-resolvable form of ARK URI'
        for identifier in self.dc.content.identifier_list:
            if 'ark:' in identifier:
                return identifier

    def rdf_dc_graph(self):
        '''Generate an :class:`rdflib.Graph` of RDF Dublin Core for use
        with unAPI and for harvest by Zotero.  Content is based on
        Volume Dublin Core content as well as Dublin Core information
        from the parent :class:`Book` object'''
        g = Graph()
        g.bind('dc', DC)
        g.bind('bibo', BIBO)
        # use ARK URI as identifier
        u = rdflib.URIRef(self.ark_uri)
        g.add((u, RDF.type, BIBO.book))

        # add information from dublin core
        dc = self.dc.content
        g.add((u, DC.title, rdflib.Literal(dc.title)))
        if self.volume:
            g.add((u, BIBO.volume, rdflib.Literal(self.volume)))
        g.add((u, DC.identifier, u))
        g.add((u, BIBO.uri, u))

        # creator info seems to be at book level, rather than volume
        for creator in dc.creator_list:
            g.add((u, DC.creator, rdflib.Literal(creator)))

        if not dc.creator_list:
            for creator in self.book.dc.content.creator_list:
                g.add((u, DC.creator, rdflib.Literal(creator)))
        # same for publisher
        if dc.publisher:
            g.add((u, DC.publisher, rdflib.Literal(dc.publisher)))
        elif self.book.dc.content.publisher:
            g.add((u, DC.publisher, rdflib.Literal(self.book.dc.content.publisher)))
        # seems to be also the case for date
        # NOTE: we have multiple dates; seems to be one for original edition
        # and one for the digitial edition. Zotero only picks up one (randomly?);
        # do we want to privilege the earlier date ?
        for d in self.date:
            g.add((u, DC.date, rdflib.Literal(d)))

        for description in dc.description_list:
            g.add((u, DC.description, rdflib.Literal(description)))
        if not dc.description_list:
            for description in self.book.dc.content.description_list:
                g.add((u, DC.description, rdflib.Literal(description)))

        if dc.format:
            g.add((u, DC['format'], rdflib.Literal(dc.format)))
            # NOTE: can't use DC.format because namespaces have a format method
        if dc.language:
            g.add((u, DC.language, rdflib.Literal(dc.language)))
        if dc.rights:
            g.add((u, DC.rights, rdflib.Literal(dc.rights)))

        for rel in dc.relation_list:
            # NOTE: tried adding PDF as RDF.value, but Zotero doesn't pick it up as an attachment
            g.add((u, DC.relation, rdflib.URIRef(rel)))

        return g

    def rdf_dc(self):
        'Serialized form of :meth:`rdf_dc_graph` for use with unAPI'
        return self.rdf_dc_graph().serialize()

    def find_solr_pages(self):
        '''Find pages for the current volume, sorted by page order; returns solr query
        for any further filtering or pagination.'''
        solr = solr_interface()
        # find all pages that belong to the same volume and sort by page order
        # - filtering separately should allow solr to cache filtered result sets more efficiently
        solrquery = solr.query(isConstituentOf=self.uri) \
                       .filter(content_model=Page.PAGE_CMODEL_PATTERN) \
                       .filter(state='A') \
                       .sort_by('page_order')
        # only return fields we actually need (pid, page_order)
        solrquery = solrquery.field_limit(['pid', 'page_order'])  # ??
        # return so it can be filtered, paginated as needed
        return solrquery

    @property
    def pdf_size(self):
        'size of the pdf, in bytes'
        # exposing as a property here for consistency with SolrVolume result
        return self.pdf.size

    @property
    def language(self):
        'language of the content'
        # exposing as a property here for consistency with SolrVolume result
        return self.dc.content.language


class VolumeV1_0(Volume):
    '''Fedora object for ScannedVolume-1.0.  Extends :class:`Volume`.'''
    #: volume content model
    VOLUME_CONTENT_MODEL = 'info:fedora/emory-control:ScannedVolume-1.0'
    CONTENT_MODELS = [ VOLUME_CONTENT_MODEL ]
    # NEW_OBJECT_VIEW = 'books:book-pages'

    # inherits dc, rels-ext, pdf

    #: :class:`~eulfedora.models.XmlDatastream` for ABBYY
    #: FineReader OCR XML; content as :class:`AbbyyOCRXml`'''
    ocr = XmlDatastream("OCR", "ABBYY Finereader OCR XML", abbyyocr.Document, defaults={
        'control_group': 'M',
        'versionable': True,
    })

    # shortcuts for consistency with SolrVolume
    #: path to xslt for transforming abbyoccr to plain text with some structure
    ocr_to_text_xsl = os.path.join(settings.BASE_DIR, 'readux', 'books', 'abbyocr-to-text.xsl')

    @property
    def fulltext_available(self):
        return self.ocr.exists

    def get_fulltext(self):
        '''Return OCR full text (if available)'''
        if self.ocr.exists:
            with open(self.ocr_to_text_xsl) as xslfile:
                try:
                    transform =  self.ocr.content.xsl_transform(filename=xslfile,
                        return_type=unicode)
                    # returns _XSLTResultTree, which is not JSON serializable;
                    # convert to unicode
                    return unicode(transform)
                except XMLSyntaxError:
                    logger.warn('OCR xml for %s is invalid', self.pid)
                    # use beautifulsoup as fallback, since it can handle invalid xml
                    # explicitly request generic ds object to avoid attempting to parse as xml
                    ds = self.getDatastreamObject(self.ocr.id, dsobj_type=DatastreamObject)
                    xmlsoup = BeautifulSoup(ds.content)
                    # simple get text seems to generate reasonable text + whitespace
                    return xmlsoup.get_text()


class VolumeV1_1(Volume):
    '''Fedora object for ScannedVolume-1.1.  Extends :class:`Volume`.'''
    #: volume content model
    VOLUME_CONTENT_MODEL = 'info:fedora/emory-control:ScannedVolume-1.1'
    CONTENT_MODELS = [ VOLUME_CONTENT_MODEL ]
    NEW_OBJECT_VIEW = 'books:volume'

    # inherits dc, rels-ext, pdf
    # no ocr datastream, because ocr is at the page level

    @property
    def fulltext_available(self):
        # volume v1.1 doesn't include the full-text anywhere at the volume level,
        # so text content is only available if pages are loaded
        return self.has_pages

    def get_fulltext(self):
        '''Return OCR full text (if available)'''
        q =  self.find_solr_pages()
        q = q.field_limit(['page_text'])
        return '\n\n'.join(p['page_text'] for p in q if 'page_text' in p)

class SolrVolume(UserDict, BaseVolume):
    '''Extension of :class:`~UserDict.UserDict` for use with Solr results
    for volume-specific content.  Extends :class:`BaseVolume` for common
    Volume fields based on existing fields such as label.
    '''

    #: fields that should be returned via Solr to support list display needs
    necessary_fields = ['pid', 'title', 'label', 'language',
        'creator', 'date', 'hasPrimaryImage',
        'page_count', 'collection_id', 'collection_label',
        'pdf_size', 'start_page', 'created'
    ]

    def __init__(self, **kwargs):
        # sunburnt passes fields as kwargs; userdict wants them as a dict
        UserDict.__init__(self, kwargs)

    @property
    def label(self):
        'object label'
        return self.data.get('label')

    @property
    def pid(self):
        'object pid'
        return self.data.get('pid')

    @property
    def has_pages(self):
        return int(self.data.get('page_count', 0)) > 1

    @property
    def language(self):
        'language of the content'
        # exposing as a property here for generating voyant url
        return self.get('language')

    @property
    def primary_image(self):
        # allow template access to cover image pid to work the same way as
        # it does with Volume - vol.primary_image.pid
        if 'hasPrimaryImage' in self.data:
            return {'pid': self.data.get('hasPrimaryImage')}

    @property
    def start_page(self):
        return self.data.get('start_page')

# hack: patch in volume as the related item type for pages
# (can't be done in page declaration due to order / volume primary image rel)
Page.volume.object_type = Volume
