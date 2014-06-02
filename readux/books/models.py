from UserDict import UserDict
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from lxml.etree import XMLSyntaxError
import logging

import rdflib
from rdflib import Graph
from rdflib.namespace import RDF

from eulfedora.models import DigitalObject, Relation, FileDatastream, \
    XmlDatastream
from eulfedora.rdfns import relsext
from eulfedora.indexdata.util import pdf_to_text

from readux.books import abbyyocr
from readux.collection.models import Collection


logger = logging.getLogger(__name__)


BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
DC = rdflib.Namespace('http://purl.org/dc/terms/')


class Book(DigitalObject):
    '''Fedora Book Object.  Extends :class:`~eulfedora.models.DigitalObject`.

    .. Note::

        This is a bare-minimum model, only implemented enough to support
        indexing and access to volumes.
    '''
    #: content model for books
    BOOK_CONTENT_MODEL = 'info:fedora/emory-control:ScannedBook-1.0'
    CONTENT_MODELS = [ BOOK_CONTENT_MODEL ]

    #: :class:`~readux.collection.models.Collection` this book belongs to
    collection = Relation(relsext.isMemberOfCollection, type=Collection)


class BaseVolume(object):
    '''Common functionality for :class:`Volume` and :class:`SolrVolume`'''

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
        current_site = Site.objects.get_current()
        return ''.join(['http://', current_site.domain,
                        reverse('books:text', kwargs={'pid': self.pid})])


class Volume(DigitalObject, BaseVolume):
    '''Fedora Volume Object.  Extends :class:`~eulfedora.models.DigitalObject`.'''
    #: volume content model
    VOLUME_CONTENT_MODEL = 'info:fedora/emory-control:ScannedVolume-1.0'
    CONTENT_MODELS = [ VOLUME_CONTENT_MODEL ]
    # NEW_OBJECT_VIEW = 'books:book-pages'

    # inherits DC, RELS-EXT
    # related to parent Book object via isConstituentOf

    #: pdf :class:`~eulfedora.models.FileDatastream` with the content
    #: of the Volume (page images with OCR text behind)
    pdf = FileDatastream("PDF", "PDF datastream", defaults={
        'mimetype': 'application/pdf',
        'versionable': True,
    })

    #: :class:`~eulfedora.models.XmlDatastream` for ABBYY
    #: FineReader OCR XML; content as :class:`AbbyyOCRXml`'''
    ocr = XmlDatastream("OCR", "ABBYY Finereader OCR XML", abbyyocr.Document, defaults={
        'control_group': 'M',
        'versionable': True,
    })

    # pages still todo
    # primary_image = Relation(REPOMGMT.hasPrimaryImage, Page, repomgmt_ns)
    # pages = ReverseRelation(relsext.isConstituentOf, Page, multiple=True)

    #: :class:`Book` this volume is associated with
    book = Relation(relsext.isConstituentOf, type=Book)

    # @permalink
    # def get_absolute_url(self):
    #     'Absolute url to view this object within the site'
    #     # currently, there is no book overview page; using all-pages view for now
    #     return ('books:book-pages', [str(self.pid)])

    # def get_pdf_url(self):
    #     return reverse('books:pdf', kwargs={'pid': self.pid})

    # @property
    # def page_count(self):
    #     'Number of pages associated with this volume, based on RELS-EXT isConstituentOf'
    #     if self.pages:
    #         return len(self.pages)

    #     # If no pages are ingested as self.pages is None, return 0
    #     return 0

    def get_fulltext(self):
        '''Return OCR full text (if available)'''
        if self.ocr.exists:
            return unicode(self.ocr.content)

    def index_data(self):
        '''Extend the default
        :meth:`eulfedora.models.DigitalObject.index_data`
        method to include additional fields specific to Volumes.'''

        data = super(Volume, self).index_data()
        if self.ocr.exists:
            try:
                data['fulltext'] = self.get_fulltext()

            except XMLSyntaxError:
                logger.warn('XML Syntax error attempting to retrieve text from OCR xml for %s' % self.pid)

        # pulling text content from the PDF is significantly slower;
        # - only pdf if ocr xml is not available or errored
        if 'fulltext' not in data:
            data['fulltext'] = pdf_to_text(self.pdf.content)

        # index primary image pid to construct urls for cover image, first page
        # if self.primary_image:
        #     data['hasPrimaryImage'] = self.primary_image.pid

        # index collection info
        data['collection_id'] = self.book.collection.pid
        # book this volume is part of, for access to book-level metadata
        data['book_id'] = self.book.pid

        # add book-level metadata to text for keyword searching purposes
        # (preliminary; may want broken out for facets/fielded searching;
        # would be better to index on book object and use joins for that if possible...)
        book_info = []
        book_info.extend(self.book.dc.content.creator_list)
        book_info.extend(self.book.dc.content.date_list)
        book_info.extend(self.book.dc.content.subject_list)
        # include collection label (short form) in fulltext search also
        book_info.append(self.book.collection.short_label)
        data['text'] = book_info

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
        for date in dc.date_list:
            g.add((u, DC.date, rdflib.Literal(date)))
        if not dc.date_list:
            for date in self.book.dc.content.date_list:
                g.add((u, DC.date, rdflib.Literal(date)))

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


class SolrVolume(UserDict, BaseVolume):
    '''Extension of :class:`~UserDict.UserDict` for use with Solr results
    for volume-specific content.  Extends :class:`BaseVolume` for common
    Volume fields based on existing fields such as label.
    '''

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



