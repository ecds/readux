from collections import defaultdict
import glob
import logging
import os
import tempfile

from PIL import Image, ImageColor
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from eulfedora.util import RequestFailed
import magic
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfpage import PDFPage

from readux.books import digwf
from readux.books.models import PageV1_0
from readux.collection.models import Collection
from readux.fedora import ManagementRepository
from readux.utils import md5sum

logger = logging.getLogger(__name__)


class BasePageImport(BaseCommand):
    '''Local extension of :class:`django.core.management.base.BaseCommand` with
    common logic for importing covers and book pages'''

    #: flag to indicate dry run/noact mode; set by :meth:`setup` based on args
    dry_run = False
    #: verbosity level; set by :meth:`setup` based on command-line arguments
    verbosity = None
    #: normal verbosity level
    v_normal = 1
    #: :class:`readux.books.digwf.Client`, initialized in :meth:`setup`
    digwf_client = None
    #: :class:`readux.fedora.ManagementRepository`, initialized in :meth:`setup`
    repo = None
    #: defaultdict to track stats about what has been done, errors, etc
    stats = defaultdict(int)

    def setup(self, **options):
        '''common setup: initialze :attr:`digwf_client` and :attr:`repo` and
        set verbosity level based on user options.'''
        self.dry_run = options.get('dry_run', False)
        self.verbosity = int(options.get('verbosity', self.v_normal))

        if not hasattr(settings, 'DIGITIZATION_WORKFLOW_API'):
            raise CommandError('DIGITIZATION_WORKFLOW_API is not configured in Django settings')

        self.digwf_client = digwf.Client(settings.DIGITIZATION_WORKFLOW_API)
        self.repo = ManagementRepository()
        # double-check the repo connection here so we can report the error cleanly,
        # rather than trying to catch the first time fedora is hit
        try:
            self.repo.api.describeRepository()
        except Exception as err:
            raise CommandError('Error connecting to Fedora at %s: %s' % \
                               (settings.FEDORA_ROOT, err))

    def pids_by_collection(self, pid):
        coll = self.repo.get_object(pid, type=Collection)
        if not coll.exists:
            self.stdout.write('Collection %s does not exist or is not accessible' % \
                              pid)

        if not coll.has_requisite_content_models:
            self.stdout.write('Object %s does not seem to be a collection' % \
                              pid)

        # NOTE: this approach may not scale for large collections
        # if necessary, use a sparql query to count and possibly return the objects
        # or else sparql query query to count and generator for the objects
        # this sparql query does what we need:
        # select ?vol
        # WHERE {
        #    ?book <fedora-rels-ext:isMemberOfCollection> <info:fedora/emory-control:LSDI-Yellowbacks> .
        #   ?vol <fedora-rels-ext:isConstituentOf> ?book
        #}
        volumes = []
        for book in coll.book_set:
            volumes.extend(book.volume_set)

        return volumes


    def is_usable_volume(self, vol):
        # if object does not exist or cannot be accessed in fedora, skip it
        if not vol.exists:
            self.stats['errors'] += 1
            if self.verbosity >= self.v_normal:
                self.stdout.write('%s does not exist' % vol.pid)
            return False
        # if object is not a volume, skip it
        elif not vol.has_requisite_content_models:
            self.stats['errors'] += 1
            if self.verbosity >= self.v_normal:
                self.stdout.write('%s is not a Volume object' % vol.pid)
            return False

        return True

    def find_page_images(self, vol):
        '''Look up an item in the DigWf by pid (noid) and find display
        images.  Returns a tuple of the list of images found (empty if none
        were found) and the info returned by :class:`readux.books.digwf.Client`.

        Raises :class:`TooManyDigWFRecords` or :class:`NoDigWFRecords` if the
        digwf api returns too many or not enough records.
        '''
        images = []
        vol_info = None

        # lookup in digwf by pid (noid)
        info = self.digwf_client.get_items(pid=vol.noid)
        if info.count != 1:
            if self.verbosity >= self.v_normal:
                if info.count > 1:
                    self.stdout.write("Error: Found more than one (%d) DigWF record for %s. This shouldn't happen!" \
                                       % (info.count, vol.pid))
                else:
                    if self.verbosity >= self.v_normal:
                        self.stdout.write("Error: No information found in DigWF for %s" % vol.pid)

            # nothing to do
            return images, vol_info

        vol_info = info.items[0]
        logger.debug("image path for %s : %s" % \
           (vol.pid, vol_info.display_image_path))

        if not vol_info.display_image_path:
            self.stdout.write('Error: no display image path set for %s' % vol.pid)
            # no images can possibly be found
            return [], vol_info

        # look for JPEG2000 images first (preferred format)
        images = glob.glob(os.path.join(vol_info.display_image_path,
                                             '*.jp2'))
        # if not found in base display path, check for a JP2 subdir
        if not len(images):
            images = glob.glob(os.path.join(vol_info.display_image_path,
                                                 'JP2', '*.jp2'))
        # if jp2s were not found in either location, look for tiffs
        if not len(images):
            images = glob.glob('%s/*.tif' % vol_info.display_image_path)

        # tif variant - in some cases, extension is upper case
        if not len(images):
            images = glob.glob('%s/*.TIF' % vol_info.display_image_path)

        # if neither jp2s nor tiffs were found, look for jpgs
        if not len(images):
            images = glob.glob('%s/*.jpg' % vol_info.display_image_path)

        # make sure the files are sorted; images are expected to be named
        # so that they are ordered in page-sequence when sorted
        images.sort()

        if not len(images):
            self.stdout.write('Error: no files matching *.jp2, *.tif, *.TIF, or *.jpg found for %s' % \
                              vol_info.display_image_path)

        # images could be empty list if no matches were found
        return images, vol_info

    #: how many pages in to look for a cover (0-based)
    cover_range = 7

    def identify_cover(self, images, pdf):
        '''Attempt to identify the image that should be used as the primary image
        for this volume.  Use PDF outline information when avialable; otherwise,
        look through the first few images and select the first non-blank one.

        Returns a tuple of the image filename and the index where it
        was found.

        :param images: list of image file paths for this volume
        :param pdf: path to the pdf file for this volume
        '''
        coverindex = self.pdf_cover(pdf, images)
        # if a cover file index was identified via PDF outline, use that
        if coverindex is not None:
            return images[coverindex], coverindex

        coverfile = coverindex = None

        for index in range(0, self.cover_range):
            imgfile = images[index]
            # first non-blank page should be the cover
            if not self.is_blank_page(imgfile):
                coverfile = imgfile
                coverindex = index
                break

        return coverfile, coverindex

    def pdf_cover(self, pdf, images):
        '''Attempt to use embedded outline information in the PDF to determine
        which image to use as the cover or primary image for the volume.

        :param pdf: path to the pdf file for this volume
        :param images: list of image file paths for this volume
        '''
        with open(pdf, 'rb') as pdf_file:
            parser = PDFParser(pdf_file)
            document = PDFDocument(parser)
            try:
                outlines = document.get_outlines()
                logger.debug('PDF %s includes outline information, using for cover identification',
                             pdf)
            except PDFNoOutlines:
                logger.debug('PDF %s does not include outline information', pdf)
                return None

            # generate a dictionary of page object id and zero-based page number
            pages = dict((page.pageid, pageno) for (pageno, page)
                  in enumerate(PDFPage.create_pages(document)))

            possible_coverpages = []
            page_count = 0
            for (level, title, dest, a, se) in outlines:

                # NOTE: some LSDI PDFs trigger a maximum recursion error in
                # pdfminer; try to avoid this by bailing out after processing
                # a set number of outline items
                # caveat: outline entries are not necessarily returned in order
                page_count += 1
                if page_count > 15:
                    break

                # title is the label of the outline element

                # dest is the target page object; apparently in some cases this can be None ?
                # if so, skip it
                if dest is None:
                    continue

                # we can probably use either Cover or Title Page; there
                # may be multiple Covers (for back cover)
                if title.lower() in ['cover', 'title page']:
                    # determine page number for the reference
                    page_num = pages[dest[0].objid]

                    # check if the page is blank, as seems to be happening in some
                    # cases for what is labeled as the cover
                    try:
                        img = images[page_num]
                    except IndexError:
                        logger.error('Not enough images for requested page number %s',
                                     page_num)
                        continue

                    if self.is_blank_page(img):
                        logger.debug('PDF outline places %s at page %s but it is blank', title, page_num)
                        # do NOT include as a possible cover page
                    else:
                        # non-blank: include as possible cover page
                        logger.debug('PDF outline places %s at page %s', title, page_num)
                        possible_coverpages.append(page_num)

            if possible_coverpages:
                # for now, just return the lowest page number, which should be
                # the first cover or title page if cover is blank
                return sorted(possible_coverpages)[0]

    def is_blank_page(self, imgfile):
        '''Check whether or not a specified image is blank.  Currently uses
        :mod:`Pillow` to determine if the image has a percentage of white over
        some threshold *or* if the image is 100% black (which seems to occur
        in some cases with two-tone jpeg2000 images).

        :param imgfile: path to the image to be checked
        :returns: boolean
        '''

        # in some cases, there are empty files; consider empty == blank
        if os.path.getsize(imgfile) == 0:
            logger.debug('%s is an empty file; considering blank', imgfile)
            return True

        img = Image.open(imgfile, mode='r')
        try:
            colors = img.getcolors()
        except Exception as err:
            logger.error('Error loading image %s: %s', imgfile, err)
            # for now, going to return true/blank if the image can't be read
            # (but this is an assumption)
            return True

        # returns a list of (count, color)
        # getcolors returns None if maxcolors (default=256) is exceeded
        if colors is None:
            colors = img.getcolors(1000000)  # set maxcolors ridiculously high
            # NOTE: colors still could be none at this point
            # For now, assuming if we can't get colors that the image is *not* blank
            if colors is None:
                logger.warn('%s has too many colors for retrieval; assuming non-blank', imgfile)
                return False

        # color white, in various formats, for comparing against colors pulled from the image
        whites = [
            255,    # not sure how this matches anything, but must be in some images
            ImageColor.colormap['white'],
            ImageColor.getrgb('white')
        ]

        blacks = [
            0,    # shows up as color value in some black/white images
            ImageColor.colormap['black'],
            ImageColor.getrgb('black')
        ]

        # percent of the page that needs to be white for it to be
        # considered blank
        blank_page_threshold = 100.0

        total, white_total, black_total = 0, 0, 0
        for count, color in colors:
            total += count
            if color in whites:
                white_total = count
            if color in blacks:
                black_total = count
        percent_white = (float(white_total) / float(total)) * 100
        percent_black = (float(black_total) / float(total)) * 100
        logger.debug('%s is %.1f%% percent white and %.1f%% black', imgfile,
                     percent_white, percent_black)

        # if percent white is over configured threshold OR if image is
        # completely black, consider it to be blank
        if percent_white >= blank_page_threshold or percent_black == 100.0:
            return True
        else:
            return False

    def convert_to_jp2(self, imgfile):
        '''Convert an image file to JPEG2000 (if it isn't already a JP2).

        Returns tuple of image file path and boolean indicating if the
        path refers to a tempfile that should be deleted after processing
        is done.
        '''
        img = Image.open(imgfile, mode='r')
        # if already jpeg200, do nothing
        if img.format == 'JPEG2000':
            return imgfile, False

        # 1-bit tiffs need to be converted before they can be saved as jp2
        if img.format == 'TIFF' and img.mode == '1':
            img = img.convert(mode='L')
        # generate tempfile to save new jp2
        tmp = tempfile.NamedTemporaryFile(prefix='readux-img-', suffix='.jp2',
            delete=False)
        img.save(tmp, format='jpeg2000')

        return tmp.name, True


    def ingest_page(self, imgfile, vol, vol_info, cover=False,
        pageindex=1, update=False, page=None):
        'Create and ingest a page object *or* update an existing page image'

        # create the page image object and associate with volume
        # calculate text & position file names
        imgbase = os.path.basename(imgfile)
        imgbasename, sep, suffix = imgbase.partition('.')
        txtfile = os.path.join(vol_info.ocr_file_path, imgbasename) + '.txt'
        posfile = os.path.join(vol_info.ocr_file_path, imgbasename) + '.pos'

        # make sure text and position files exist; if they don't, bail out
        if not os.path.exists(txtfile):
            if self.verbosity >= self.v_normal:
                self.stdout.write('Error: text file %s does not exist; skipping\n' % txtfile)
            return
        if not os.path.exists(posfile):
            if self.verbosity >= self.v_normal:
                self.stdout.write('Error: position %s file does not exist; skipping \n' % posfile)
            return
        # if the image file is zero-size (which apparently happens sometimes?), skip
        if os.path.getsize(imgfile) == 0:
            if self.verbosity >= self.v_normal:
                self.stdout.write('Error: image file %s is zero-size; skipping \n' % imgfile)
            return


        # If image is not already jpeg200, convert it before ingest
        imgfile, jp2_tmpfile = self.convert_to_jp2(imgfile)
        # NOTE: jp2 support in Pillow requires additional libraries,
        # TODO: document openjpeg installation!

        if self.verbosity > self.v_normal:
            self.stdout.write('Ingesting page %s' % imgfile)
            self.stdout.write('  text: %s\n' % txtfile)

        if page is None:
            page = self.repo.get_object(type=PageV1_0)
        # object label based on volume label (ocm# + volume info)
        page.label = '%s page %d' % (vol.label, pageindex)
        # set the relation to the volume object
        page.volume = vol
        # set a dc:title based on volume title
        page.dc.content.title = '%s page %d' % (vol.dc.content.title, pageindex)

        # set page order
        page.page_order = pageindex
        logger.debug('page %d rels-ext:%s',
           pageindex, page.rels_ext.content.serialize(pretty=True))

        if not self.dry_run:
            # calculate checksums and mimetypes for ingest
            m = magic.Magic(mime=True)

            dsfiles = {
                page.image: imgfile,
                page.text: txtfile,
                page.position: posfile
                }
            open_files = []

            for ds, filepath in dsfiles.iteritems():
                # calculate checksum
                checksum = md5sum(filepath)
                # if this an update and the checksums match, don't modify the datastream
                if update and checksum == ds.checksum:
                    continue
                ds.checksum = md5sum(filepath)
                logger.debug('checksum for %s is %s',
                            filepath, ds.checksum)
                ds.checksum_type = 'MD5'

                # make sure image mimetype gets set correctly (should be image/jp2)
                # most reliable, general way to do this is to set mimetype based on mime magic
                mimetype = m.from_file(filepath)
                mimetype, separator, options = mimetype.partition(';')
                ds.mimetype = mimetype

                # set datastream content
                openfile = open(filepath)
                open_files.append(openfile)
                ds.content = openfile

                # NOTE: removed code from readux v1 for optional file-uri based ingest

            try:
                # if this is not an update OR if the existing object has been
                # modified, ingest/update in Fedora
                ingested = False
                if not update or any([page.image.isModified(),
                                     page.text.isModified(), page.position.isModified()]):

                    ingested = page.save('ingesting page image %d for %s' \
                                         % (pageindex, vol.pid))
                    verb = 'updated' if update else 'ingested'
                    logger.debug('page %s %s', page.pid, verb)
                    self.stats['pages'] += 1

                elif update:
                    if self.verbosity >= self.v_normal:
                        self.stdout.write('No updates needed for %s' % page.pid)

                # if a temporary file was created, remove it
                if jp2_tmpfile:
                    logger.debug('removing temporary JPEG2000 file %s', imgfile)
                    os.remove(imgfile)

            except RequestFailed as rf:
                self.stats['errors'] += 1
                self.stdout.write('Failed to ingest page image: %s\n' % rf)
                ingested = False
                self.stats['page_errors'] += 1

            finally:
                # close any local files that were opened for ingest
                for of in open_files:
                    of.close()

            # if ingesting a cover and ingest succeeded, update volume
            # object with cover relation *unless* this is an update
            if cover and ingested and not update:
                try:
                    # set current page as primary image for this volume
                    vol.primary_image = page
                    vol.rels_ext.save('adding relation to cover page object')
                    self.stats['updated'] += 1
                    if self.verbosity > self.v_normal:
                        self.stdout.write('Updated Volume %s with primary image relation to %s' % \
                                          (vol.pid, page.pid))

                except RequestFailed as rf:
                    self.stats['errors'] += 1
                    self.stdout.write('Failed to update volume %s with relation to cover %s : %s' \
                                      % (vol.pid, page.pid, rf))
