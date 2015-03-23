'''
This manage.py command should be used for loading page images for selected
volumes and collections into Readux.  Note that covers *must* be loaded
before full page-image content can be loaded for a Volume.  It is recommended
to check that covers have been detected correctly for a volume before loading pages,
since correcting the cover after all pages are loaded may be difficult.

Like :mod:`~readux.books.management.commands.import_covers`, this script
requires access to the Digitization Workflow application; the REST
endpoint should be configured in localsettings via **DIGITIZATION_WORKFLOW_API**
and image paths referenced in the Digitization Workflow application should be
mounted locally at the same path, in order to access and identify page
image content.

Finding and loading page images into Fedora is a slow process.  If you want to
load more pages at once you may find it useful to run the script in collection
mode (load pages for all volumes in a specific collection), e.g.::

    python manage.py import_pages -c emory-control:LSDI-Yellowbacks

Then you can run multiple versions of the script in parallel, so that multiple
collections can be loaded at once.  It is recommended to use the `screen` command
to manage multiple instances of the script running on a remote server, both to
avoid the script being interrupted by a connection error, and so you can easily
check on and manage multiple instances of the script running at once.

This script does have an interrupt handler configured, so if you need to stop
the import while it is in progress (e.g., if you know the Fedora Repository
needs to be restarted), first try a single control-c which will attempt to exit
cleanly after loading all pages for the current volume, and should report on
what was completed before the interruption.

.. Note::

    There is currently no mechanism for recovering or cleaning up if the script
    is interrupted part of the way through loading pages for a volume; cleaning
    up will either require manual effort or an update to this script.

----

'''
import logging
from optparse import make_option
import os
import signal
import sys

from django.core.management.base import BaseCommand, CommandError
from progressbar import ProgressBar, Bar, Percentage, \
         ETA, Counter, Timer

from readux.books.models import VolumeV1_0
from readux.books.management.page_import import BasePageImport
from readux.utils import md5sum

logger = logging.getLogger(__name__)


class Command(BasePageImport):
    '''Ingest cover images for Volume objects in Fedora.  This script requires
that cover images have already been ingested with **import_covers** script.
Requires a list of pids (will *not* ingest pages for all Volume objects in
the configured fedora instance).'''
    help = __doc__

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n',
            action='store_true',
            default=False,
            help='Don\'t make any changes; just report on what would be done'),
        make_option('--collection', '-c',
            help='Find and process volumes that belong to the specified collection pid ' + \
            '(list of pids on the command line takes precedence over this option)'),
        make_option('-f', '--fix-missing', action='store_true', default=False,
            dest='fix_missing', help='Fix volumes with partial page content loaded')
        )

    v_normal = 1

    interrupted = False
    current_volume = None
    pageindex = None
    images = None
    total = 0

    def handle(self, *pids, **options):
        # bind a handler for interrupt signal
        signal.signal(signal.SIGINT, self.interrupt_handler)

        self.setup(**options)

        # if pids are specified on command line, only process those objects
        if pids:
            objs = [self.repo.get_object(pid, type=VolumeV1_0) for pid in pids]

        # if collection is specified, find pids by collection
        elif options['collection']:
            objs = self.pids_by_collection(options['collection'])

        # otherwise, error
        else:
            raise CommandError('Please specify one or more volume pids')

        self.total = len(objs)

        vol_pbar = None
        if self.total >= 3 and os.isatty(sys.stderr.fileno()):
            # init progress bar if we're indexing enough items to warrant it
            vol_pbar = ProgressBar(widgets=['Volumes: ', Percentage(),
                                            ' (', Counter(), ')',
                                            Bar(),
                                            ETA()],
                                   maxval=self.total).start()

        for vol in objs:
            # if a SIGINT was received while ingesting pages for the last volume, stop now
            if self.interrupted:
                break

            self.stats['vols'] += 1
            # if object does not exist or cannot be accessed in fedora, skip it
            if not self.is_usable_volume(vol):
                continue

            # if volume does *not*  have a cover, don't process
            if not vol.primary_image:
                self.stats['skipped'] += 1
                if self.verbosity >= self.v_normal:
                    self.stdout.write('%s does not have a cover image; please ingest with import_covers script' % \
                        vol.pid)
                continue

            # progress bar needs to be updated *after* processing/error output
            if vol_pbar:
                # -1 because counter increments at beginning of loop
                vol_pbar.update(self.stats['vols'] - 1)

            # store volume, images, and processing index for access
            # by interrupt handler
            self.current_volume = vol
            self.pageindex = None
            self.images = None

            self.images, vol_info = self.find_page_images(vol)
            # if either images or volume info were not found, skip
            if not self.images or not vol_info:
                self.stats['skipped'] += 1   # or error?
                continue

            # cover detection (currently first non-blank page)
            coverfile, coverindex = self.identify_cover(self.images, vol_info.pdf)
            # use cover detection to determine where to start ingesting
            # - we want to start at coverindex + 1

            # if a non-blank page was not found in the first 5 pages,
            # report as an error and skip this volume
            if coverindex is None:
                self.stats['skipped'] += 1
                if self.verbosity >= self.v_normal:
                    self.stdout.write('Error: could not identify cover page in first %d images; skipping' % \
                                      self.cover_range)
                continue        # skip to next volume

            # Find the last page to ingest. If the last page is blank,
            # don't include it.
            lastpage_index = len(self.images)
            imgfile = self.images[lastpage_index-1]
            if self.is_blank_page(imgfile):
                lastpage_index -= 1

            # if the volume already has pages, check if they match
            expected_pagecount = len(self.images[coverindex:lastpage_index])
            logger.debug('Expected page count for %s is %d', vol.pid, expected_pagecount)
            if vol.page_count > 1:    # should have at least 1 for cover
                skip = True
                # if the number of pages doesn't match what we expect, error
                if vol.page_count != expected_pagecount:
                    msg = 'Error! Volume %s already has pages, but ' + \
                          'the count (%d) does not match expected value (%d); %s'
                    print >> self.stdout, \
                          msg % (vol.pid, vol.page_count, expected_pagecount,
                                'repairing' if options['fix_missing'] else '; use --fix-missing to correct')
                    if options['fix_missing']:
                        startindex, startpage = self.find_next_page(vol,
                            coverindex, self.images)
                        if startindex is None:
                            print >> self.stdout, \
                                'Could not determine next page to import'
                        else:
                            self.pageindex = startpage
                            skip = False

                # otherwise, all is well
                elif self.verbosity >= self.v_normal:
                    print >> self.stdout, \
                              'Volume %s has expected number of pages (%d) - skipping' % \
                              (vol.pid, vol.page_count)

                # skip unless repairing incomplete page load
                if skip:
                    self.stats['skipped'] += 1
                    continue

            else:
                # normal page ingest behavior
                # ingest pages as volume constituents, starting with the first image after the cover
                # - index into array of image files
                startindex = coverindex + 1
                # page order for the page
                self.pageindex = 2
                # store repo page order starting with 1, no matter what the actual index
                # page index 1 is the cover image

            # if we have received a SIGINT during this loop, stop *before* ingesting any pages;
            # break out of volume loop and report on what was done
            if self.interrupted:
                break

            page_pbar = None
            # NOTE: possibly disable page progress bar when dry-run verbose=2
            if os.isatty(sys.stderr.fileno()):
                total = expected_pagecount
                # init progress bar if we're indexing enough items to warrant it
                widgets = ['%s pages: ' % vol.pid, Percentage(),
                           ' (', Counter(), ')', Bar(), Timer()]
                page_pbar = ProgressBar(widgets=widgets, maxval=total).start()

            for index in range(startindex, lastpage_index):
                if page_pbar:
                    page_pbar.update(self.pageindex)

                imgfile = self.images[index]
                self.ingest_page(imgfile, vol, vol_info, pageindex=self.pageindex)
                # increment for next page
                self.pageindex += 1


        if vol_pbar and not self.interrupted:
            vol_pbar.finish()

        if self.verbosity >= self.v_normal:
            self.stdout.write('\n%(vols)d volume(s); %(errors)d error(s), %(skipped)d skipped, %(updated)d updated' % \
                self.stats)
            if self.stats['pages']:
                self.stdout.write('%(pages)d page(s) ingested' % self.stats)

    def find_next_page(self, vol, coverindex, images):
        '''Determien the index and page order of the next page to be ingested
        when a volume has incomplete pages, e.g. when page import was
        previously interrupted.'''
        next_index = vol.page_count + coverindex
        logger.debug('cover index is %d, current page count is %d; expected next page index %d',
            coverindex, vol.page_count, next_index)

        # pages are currently not guaranteed to be returned in order,
        # so generate a dictionary so we can find the last checksum
        # NOTE: this is potentially slow for large volumes...
        pages = sorted(vol.pages, key=lambda p: p.page_order)
        last_page = pages[-1]

        # check that checksum for last page matches
        last_image = images[next_index - 1]
        # generate a checksum for the image as it would be ingested
        # (i.e., convert to jpeg2000 if necessary)
        tmpname, delete = self.convert_to_jp2(last_image)
        checksum = md5sum(tmpname)
        # delete tmpfile if one was created
        if delete:
            os.remove(tmpname)

        # if the checksums match, then expected next index is correct

        logger.debug('Image checksum for last ingested page %s is %s; calculated checksum is %s',
            last_page.pid, last_page.image.checksum, checksum)

        if checksum == last_page.image.checksum:
            # return image index and numerical page order for next page
            return (next_index, pages[-1].page_order + 1)

        # otherwise, return nothing (next page information not found)


    def interrupt_handler(self, signum, frame):
        '''Gracefully handle a SIGINT, if possible.  Reports status if
        main loop is currently part-way through pages for a volume,
        sets a flag so main script loop can exit cleanly, and restores
        the default SIGINT behavior, so that a second interrupt will
        stop the script.
        '''
        if signum == signal.SIGINT:
            # restore default signal handler so a second SIGINT can be used to quit
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            # set interrupt flag so main loop knows to quit at a reasonable time
            self.interrupted = True
            # report if script is in the middle of ingesting pages for a volume
            if self.pageindex and self.images:
                print >> self.stdout, \
                      '\nProcessing %d of %d pages for volume %s.' % \
                      (self.pageindex, len(self.images), self.current_volume)
                print >> self.stdout, \
                      'Script will exit after all pages for the current volume are processed.'
                print >> self.stdout, '(Ctrl-C / Interrupt again to quit now)'

            else:
                msg = '''\nProcessing %d of %d volumes; script will exit before %s page ingest starts or after it is complete.
(Ctrl-C / Interrupt again to quit immediately)'''
                print >> self.stdout, msg % (self.stats['vols'], self.total, self.current_volume)
