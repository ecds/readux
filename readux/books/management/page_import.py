from collections import defaultdict
import glob
import logging
import os
import tempfile

from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from eulfedora.util import RequestFailed
import magic

from readux.books import digwf
from readux.books.models import Page
from readux.fedora import ManagementRepository
from readux.utils import md5sum

logger = logging.getLogger(__name__)


class BasePageImport(BaseCommand):
    # common logic for importing covers and book pages

    def setup(self, **options):
        self.dry_run = options.get('dry_run', False)
        self.verbosity = int(options.get('verbosity', self.v_normal))

        if not hasattr(settings, 'DIGITIZATION_WORKFLOW_API'):
            raise CommandError('DIGITIZATION_WORKFLOW_API is not configured in Django settings')

        self.digwf_client = digwf.Client(settings.DIGITIZATION_WORKFLOW_API)
        self.repo = ManagementRepository()

        self.stats = defaultdict(int)

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

        # make sure the files are sorted; images are expected to be named
        # so that they are ordered in page-sequence when sorted
        images.sort()

        if not len(images):
            self.stdout.write('Error: no files matching *.tif or *.jp2 found for %s' % \
                              vol_info.display_image_path)

        # images could be empty list if no matches were found
        return images, vol_info

    #: how many pages in to look for a cover (0-based)
    cover_range = 4

    def identify_cover(self, images):
        '''Look through the first few images; the first non-blank
        one should be the cover.

        Returns a tuple of the image filename and the index where it
        was found.
        '''
        coverfile = coverindex = None

        for index in range(0, self.cover_range):
            imgfile = images[index]
            # first non-blank page should be the cover
            if not self.is_blank_page(imgfile):
                coverfile = imgfile
                coverindex = index
                break

        return coverfile, coverindex

    def is_blank_page(self, imgfile):
        '''Check whether or not a specified image is blank.'''

        # in some cases, there are empty files; consider empty == blank
        if os.path.getsize(imgfile) == 0:
            logger.debug('%s is an empty file; considering blank')
            return True

        img = Image.open(imgfile, mode='r')
        colors = img.getcolors()
        # getcolors returns None if maxcolors (default=256) is exceeded
        if colors is None:
            colors = img.getcolors(1000000)  # set maxcolors ridiculously high
            # FIXME: colors still could be none at this point
            # -- if so, can we assume not blank?

        # returns a list of (count, pixel)
        white = 255
        # percent of the page that needs to be white for it to be
        # considered blank
        blank_page_threshold = 100.0

        total, white_total = 0, 0
        for count, color in colors:
            total += count
            if color == white:
                white_total = count
        percent_white = (float(white_total) / float(total)) * 100
        logger.debug('%s is %.1f%% percent white' % (imgfile, percent_white))

        if percent_white >= blank_page_threshold:
            return True
        else:
            return False

    def convert_to_jp2(self, imgfile):
        ''''Convert an image file to JPEG2000 if it isn't already.

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
        pageindex=1):
        'Create and ingest a page object'

        # create the page image object and associate with volume
        # calculate text & position file names
        imgbase = os.path.basename(imgfile)
        imgbasename, sep, suffix = imgbase.partition('.')
        txtfile = os.path.join(vol_info.ocr_file_path, imgbasename) + '.txt'
        posfile = os.path.join(vol_info.ocr_file_path, imgbasename) + '.pos'

        if self.verbosity >= self.v_normal:
            if not os.path.exists(txtfile):
                self.stdout.write('Error: text file does not exist %s\n' % txtfile)
            if not os.path.exists(posfile):
                self.stdout.write('Error: position file does not exist %s\n' % posfile)

        # If image is not already jpeg200, convert it before ingest
        imgfile, jp2_tmpfile = self.convert_to_jp2(imgfile)
        # NOTE: jp2 support in Pillow requires additional libraries,
        # TODO: document openjpeg installation!

        if self.verbosity > self.v_normal:
            self.stdout.write('Ingesting page %s' % imgfile)
            self.stdout.write('  text: %s\n' % txtfile)

        page = self.repo.get_object(type=Page)
        # object label based on volume label (ocm# + volume info)
        page.label = '%s page %d' % (vol.label, pageindex)
        # set the relation to the volume object
        page.volume = vol
        # set a dc:title based on volume title
        page.dc.content.title = '%s page %d' % (vol.dc.content.title, pageindex)

        # set page order
        page.page_order = pageindex
        logger.debug('page %d rels-ext:%s' % \
           (pageindex, page.rels_ext.content.serialize(pretty=True)))

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
                ds.checksum = md5sum(filepath)
                logger.debug('checksum for %s is %s' % \
                            (filepath, ds.checksum))
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
                ingested = page.save('ingesting page image %d for %s' \
                                     % (pageindex, vol.pid))
                logger.debug('page ingested as %s' % page.pid)
                self.stats['pages'] += 1

                # if a temporary file was created, remove it
                if jp2_tmpfile:
                    logger.debug('removing temporary JPEG2000 file %s' % imgfile)
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
            # object with cover relation
            if cover and ingested:
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


