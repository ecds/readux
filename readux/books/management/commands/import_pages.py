import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

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

    def handle(self, *pids, **options):
        self.setup(**options)

        # if pids are specified on command line, only process those objects
        if pids:
            objs = [self.repo.get_object(pid, type=Volume) for pid in pids]

        # otherwise, error
        else:
            raise CommandError('Please specify one or more volume pids')

        for vol in objs:
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

            images, vol_info = self.find_page_images(vol)
            # if either images or volume info were not found, skip
            if not images or not vol_info:
                self.stats['skipped'] += 1   # or error?
                continue

            # cover detection (currently first non-blank page)
            coverfile, coverindex = self.identify_cover(images)
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
            lastpage_index = len(images)
            imgfile = images[lastpage_index-1]
            if self.is_blank_page(imgfile):
                lastpage_index -= 1

            # if the volume already has pages, check if they match
            expected_pagecount = len(images[coverindex:lastpage_index])
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
            pageindex = 1  # store repo page order starting with 1, no matter what the actual index
            # page index 1 is the cover image

            # progressbar todo?

            for index in range(coverindex + 1, lastpage_index):
                pageindex += 1
                imgfile = images[index]
                self.ingest_page(imgfile, vol, vol_info, pageindex=pageindex)


        if self.verbosity >= self.v_normal:
            self.stdout.write('\n%(vols)d volume(s); %(errors)d error(s), %(skipped)d skipped, %(updated)d updated' % \
                self.stats)
            if self.stats['pages']:
                self.stdout.write('%(pages)d page(s) ingested' % self.stats)





