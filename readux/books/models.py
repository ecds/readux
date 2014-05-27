from UserDict import UserDict
from eulfedora.models import DigitalObject, Relation, FileDatastream, \
    XmlDatastream
from eulfedora.rdfns import relsext
from eulfedora.indexdata.util import pdf_to_text

from readux.books import abbyyocr
from readux.collection.models import Collection



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
            data['fulltext'] = self.get_fulltext()
        # # pulling text content from the PDF is significantly slower;
        # # - only pdf if ocr xml is not available
        # elif self.pdf.exists:
        #     data['fulltext'] = pdf_to_text(self.pdf.content)

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



