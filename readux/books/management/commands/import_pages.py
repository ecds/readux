import logging
from optparse import make_option
import os
import signal
import sys

from django.core.management.base import BaseCommand, CommandError
from progressbar import ProgressBar, Bar, Percentage, \
         ETA, Counter, Timer

from readux.books.models import Volume
from readux.books.management.page_import import BasePageImport


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
        )

    v_normal = 1

    interrupted = False

    def handle(self, *pids, **options):
        # bind a handler for interrupt signal
        signal.signal(signal.SIGINT, self.interrupt_handler)

        self.setup(**options)

        # if pids are specified on command line, only process those objects
        if pids:
            objs = [self.repo.get_object(pid, type=Volume) for pid in pids]

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
            logger.debug('Expected page count for %s is %d' % (vol.pid, expected_pagecount))
            if vol.page_count > 1:    # should have at least 1 for cover
                # if the number of pages doesn't match what we expect, error
                if vol.page_count != expected_pagecount:
                    msg = 'Error! Volume %s already has pages, but ' + \
                          'the count (%d) does not match expected value (%d)'
                    print >> self.stdout, \
                          msg % (vol.pid, vol.page_count, expected_pagecount)

                # otherwise, all is well
                elif self.verbosity >= self.v_normal:
                    print >> self.stdout, \
                              'Volume %s has expected number of pages (%d) - skipping' % \
                              (vol.pid, vol.page_count)

                # either way, no further processing
                self.stats['skipped'] += 1
                continue

            # ingest pages as volume constituents, starting with the first image after the cover
            self.pageindex = 1  # store repo page order starting with 1, no matter what the actual index
            # page index 1 is the cover image

            # progressbar todo?

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

            for index in range(coverindex + 1, lastpage_index):
                self.pageindex += 1
                if page_pbar:
                    page_pbar.update(self.pageindex)

                imgfile = self.images[index]
                self.ingest_page(imgfile, vol, vol_info, pageindex=self.pageindex)


        if vol_pbar and not self.interrupted:
            vol_pbar.finish()

        if self.verbosity >= self.v_normal:
            self.stdout.write('\n%(vols)d volume(s); %(errors)d error(s), %(skipped)d skipped, %(updated)d updated' % \
                self.stats)
            if self.stats['pages']:
                self.stdout.write('%(pages)d page(s) ingested' % self.stats)


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
