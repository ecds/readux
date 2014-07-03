from collections import defaultdict
import glob
import logging
import os
from optparse import make_option

from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from eulfedora.util import RequestFailed

from readux.books import digwf
from readux.books.models import Volume, Page
from readux.fedora import ManagementRepository
from readux.utils import md5sum


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''Update LSDI Volume PDF ARKs to resolve to the current readux site.
Takes an optional list of pids; otherwise, looks for all Volume objects in
the configured fedora instance.'''
    help = __doc__

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n',
            action='store_true',
            default=False,
            help='Don\'t make any changes; just report on what would be done'),
        )

    v_normal = 1

    def handle(self, *pids, **options):

        dry_run = options.get('dry_run', False)
        verbosity = int(options.get('verbosity', self.v_normal))

        if not hasattr(settings, 'DIGITIZATION_WORKFLOW_API'):
            raise CommandError('DIGITIZATION_WORKFLOW_API is not configured in Django settings')

        digwf_client = digwf.Client(settings.DIGITIZATION_WORKFLOW_API)

        repo = ManagementRepository()
        # if pids are specified on command line, only process those objects
        if pids:
            objs = [repo.get_object(pid, type=Volume) for pid in pids]

        # otherwise, look for all volume objects in fedora
        else:
            objs = repo.get_objects_with_cmodel(Volume.VOLUME_CONTENT_MODEL,
                                                type=Volume)

        stats = defaultdict(int)
        for vol in objs:
            stats['vols'] += 1
            # if object does not exist or cannot be accessed in fedora, skip it
            if not vol.exists:
                stats['errors'] += 1
                if verbosity >= self.v_normal:
                    self.stdout.write('%s does not exist' % vol.pid)
                continue

            # if volume already has a cover, don't re-ingest
            if vol.primary_image:
                stats['skipped'] += 1
                if verbosity >= self.v_normal:
                    self.stdout.write('%s already has a cover image %s' % \
                        (vol.pid, vol.primary_image.pid))
                continue

            # lookup in digwf by pid (noid)
            info = digwf_client.get_items(pid=vol.noid)
            if info.count != 1:
                if verbosity >= self.v_normal:
                    if info.count > 1:
                        self.stdout.write("Error: Found more than one (%d) DigWF record for %s. This shouldn't happen!" \
                                          % (info.count, vol.pid))
                    else:
                        self.stdout.write("Error: No information found in DigWF for %s" % vol.pid)

                # skip to next volume
                continue

            vol_info = info.items[0]
            logger.debug("image path for %s : %s" % \
                         (vol.pid, vol_info.display_image_path))
            # look for JPEG2000 images first (preferred format)
            self.images = glob.glob(os.path.join(vol_info.display_image_path,
                                                 '*.jp2'))
            # if not found in base display path, check for a JP2 subdir
            if not len(self.images):
                self.images = glob.glob(os.path.join(vol_info.display_image_path,
                                                     'JP2', '*.jp2'))
            # if jp2s were not found in either location, look for  tiffs
            if not len(self.images):
                self.images = glob.glob('%s/*.tif' % vol_info.display_image_path)
            # make sure the files are sorted; images are expected to be named
            # so that they are ordered in page-sequence when sorted
            self.images.sort()
            if not len(self.images):
                self.stdout.write('Error: no files matching *.tif or *.jp2 at %s' % \
                          vol_info.display_image_path)
                continue        # nothing to do, skip to next volume

            # TODO: could we also use this logic to calculate and store
            # what page the PDF should be opened to?

            # TODO: move cover detection logic into separate method

            # Look through the first few images; the first non-blank
            # one should be the cover.
            coverfile = None
            coverindex = None
            cover_range = 4     # how many pages to look for a cover
            for index in range(0, cover_range):
                imgfile = self.images[index]
                # first non-blank page should be the cover
                if not self.is_blank_page(imgfile):
                    coverfile = imgfile
                    coverindex = index  # store cover page index
                    break

            # if a non-blank page was not found in the first 5 pages,
            # report as an error and skip this volume
            if coverindex is None:
                if verbosity >= self.v_normal:
                    self.stdout.write('Error: could not identify cover page in first %d images; skipping' % \
                                      cover_range)
                continue        # skip to next volume


            # TODO: move ingest logic into separate method

            # create the page image object and associate with volume
            # calculate text & position file names
            imgbase = os.path.basename(coverfile)
            imgbasename, sep, suffix = imgbase.partition('.')
            txtfile = os.path.join(vol_info.ocr_file_path, imgbasename) + '.txt'
            posfile = os.path.join(vol_info.ocr_file_path, imgbasename) + '.pos'

            if verbosity >= self.v_normal:
                if not os.path.exists(txtfile):
                    self.stdout.write('Error: text file does not exist %s\n' % txtfile)
                if not os.path.exists(posfile):
                    self.stdout.write('Error: position file does not exist %s\n' % posfile)

            # TODO: if images are not already jpeg2000, convert them
            # NOTE: jp2 support in Pillow requires additional libraries,
            # figure out how to get this installed on osx
            if verbosity > self.v_normal:
                self.stdout.write('Ingesting %s as cover' % coverfile)
                self.stdout.write('  text: %s\n' % txtfile)

            pageindex = 0  # store page order starting with 1, no matter what the actual index
            # (will be important once we add pages other than cover)

            page = repo.get_object(type=Page)
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

            if not dry_run:
                # calculate checksums for ingest
                dsfiles = {
                    page.image: imgfile,
                    page.text: txtfile,
                    page.position: posfile
                    }
                open_files = []

                for ds, filepath in dsfiles.iteritems():
                    # NOTE: Due to a bug in Fedora (affects 3.4,
                    # 3.5), content cannot be ingested from a
                    # file:// URI with a checksum value; as a
                    # temporary measure, do not calculate or send
                    # the checksum; just let Fedora calculate and
                    # store one.
                    # https://jira.duraspace.org/browse/FCREPO-787
                    if not options.get('file_uris', False):
                        ds.checksum = md5sum(filepath)
                        logger.debug('checksum for %s is %s' % \
                                    (filepath, ds.checksum))
                    ds.checksum_type = 'MD5'

                # NOTE: code from readux v1; do we want to support this?
                # not currently exposed on options; might require configurable fedora base path
                # if requested, ingest by local file URIs on fedora server
                if options.get('file_uris', False):
                    for dsobj, file in dsfiles.iteritems():
                        dsobj.ds_location = 'file://%s' % file
                        logger.debug('setting %s location to %s' % \
                                    (dsobj.id, dsobj.ds_location))

                # otherwise read the files and post the contents
                else:
                    for ds, filepath in dsfiles.iteritems():
                        openfile = open(filepath)
                        open_files.append(openfile)
                        ds.content = openfile

                try:
                    ingested = page.save('ingesting page image %d for %s' \
                                         % (pageindex, vol.pid))
                    logger.debug('page ingested as %s' % page.pid)
                    stats['pages'] += 1
                except RequestFailed as rf:
                    stats['errors'] += 1
                    self.stdout.write('Failed to ingest page image: %s\n' % rf)
                    ingested = False
                    stats['page_errors'] += 1

                finally:
                    # close any local files that were opened for ingest
                    for of in open_files:
                        of.close()

                # if the ingest succeeded, update volume object with cover relation
                if ingested:
                    try:
                        # set current page as primary image for this volume
                        vol.primary_image = page
                        vol.rels_ext.save('adding relation to cover page object')
                        stats['updated'] += 1
                        if verbosity > self.v_normal:
                            self.stdout.write('Updated Volume %s with primary image relation to %s' % \
                                              (vol.pid, page.pid))

                    except RequestFailed as rf:
                        stats['errors'] += 1
                        self.stdout.write('Failed to update volume %s with relation to cover %s : %s' \
                                          % (vol.pid, page.pid, rf))

        if verbosity >= self.v_normal:
            self.stdout.write('\n%(vols)d volume(s); %(errors)d error(s), %(skipped)d skipped, %(updated)d updated' % \
                stats)


    def is_blank_page(self, imgfile):
        img = Image.open(imgfile, mode='r')
        colors = img.getcolors()
        # getcolors returns None if maxcolors (default=256) is exceeded
        if colors is None:
            colors = img.getcolors(1000000)  # set maxcolors ridiculously high

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

