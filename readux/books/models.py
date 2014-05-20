from eulfedora.models import DigitalObject, Relation, FileDatastream, \
    XmlDatastream
from eulfedora.rdfns import relsext

from readux.collection.models import Collection


class Book(DigitalObject):
    '''Fedora Book Object.  Extends :class:`~eulfedora.models.DigitalObject`.

    .. Note::

        This is a bare-minimum model, only implemented enough to support
        indexing and access to volumes.
    '''
    BOOK_CONTENT_MODEL = 'info:fedora/emory-control:ScannedBook-1.0'
    CONTENT_MODELS = [ BOOK_CONTENT_MODEL ]

    collection = Relation(relsext.isMemberOfCollection, type=Collection)

class Volume(DigitalObject):
    '''Fedora Volume Object.  Extends :class:`~eulfedora.models.DigitalObject`.'''
    VOLUME_CONTENT_MODEL = 'info:fedora/emory-control:ScannedVolume-1.0'
    CONTENT_MODELS = [ VOLUME_CONTENT_MODEL ]
    # NEW_OBJECT_VIEW = 'books:book-pages'

    # inherits DC, RELS-EXT
    # related to parent Book object via isConstituentOf

    pdf = FileDatastream("PDF", "PDF datastream", defaults={
        'mimetype': 'application/pdf',
        'versionable': True,
    })
    '''pdf :class:`~eulfedora.models.FileDatastream` with the content
    of the Volume (page images with OCR text behind'''

    # ABBYY FineReader OCR XML is available as OCR datastream
    ocr = XmlDatastream("OCR", "ABBYY Finereader OCR XML", abbyyocr.Document, defaults={
        'control_group': 'M',
        'versionable': True,
    })
    ''':class:`~eulfedora.models.XmlDatastream` for ABBYY
    FineReader OCR XML; content as :class:`AbbyyOCRXml`'''

    # pages still todo
    # primary_image = Relation(REPOMGMT.hasPrimaryImage, Page, repomgmt_ns)
    # pages = ReverseRelation(relsext.isConstituentOf, Page, multiple=True)

    book = Relation(relsext.isConstituentOf, type=Book)

    @permalink
    def get_absolute_url(self):
        'Absolute url to view this object within the site'
        # currently, there is no book overview page; using all-pages view for now
        return ('books:book-pages', [str(self.pid)])

    def get_pdf_url(self):
        return reverse('books:pdf', kwargs={'pid': self.pid})

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
        pidspace, sep, noid = self.pid.partition(':')
        return noid

    @property
    def page_count(self):
        'Number of pages associated with this volume, based on RELS-EXT isConstituentOf'
        if self.pages:
            return len(self.pages)

        # If no pages are ingested as self.pages is None, return 0
        return 0

    def get_fulltext(self):
        '''Return OCR full text (if available)'''
        if self.ocr.exists:
            return unicode(self.ocr.content)

    def index_data(self):
        '''Extend the default
        :meth:`eulfedora.models.DigitalObject.index_data`
        method to include additional fields specific to Book
        objects.'''

        data = super(Volume, self).index_data()
        if self.ocr.exists:
            data['fulltext'] = self.get_fulltext()
        # pulling text content from the PDF is significantly slower;
        # - only pdf if ocr xml is not available
        elif self.pdf.exists:
            data['fulltext'] = pdf_to_text(self.pdf.content)

        # index primary image pid to construct urls for cover image, first page
        if self.primary_image:
            data['hasPrimaryImage'] = self.primary_image.pid

        # index collection info
        data['collection_id'] = self.book.collection.pid
        data['collection'] = self.book.collection.short_label()


        return data