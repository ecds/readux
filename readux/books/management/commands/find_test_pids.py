'''
Manage command for generating a list of test objects, e.g. to synchronize
real content from production to QA.  Takes a text file as input with a
list of volume pids and outputs a list of all associated pids for those
objects - books, volumes, and pages (if any).  Any non-volume or
non-existent objects will be skipped; use a higher verbosity level to
see details.

Sample usage::

    python manage.py find_test_pids vol_pids.txt --calculate-size > vol_assoc_pids.txt


'''
from collections import defaultdict
import time

from django.template.defaultfilters import filesizeformat, pluralize
from django.core.management.base import BaseCommand
from eulfedora.server import Repository

from readux.books.models import Volume
from readux.fedora import ManagementRepository


class Command(BaseCommand):
    '''Generate a list of pids for testing purposes.  Takes a text file
    as input with a list of Volume pids, one per line.  Generates a list
    of all associated pids (books and pages), and can optionally
    calculate and report total approximate size of all objects listed.
    '''
    help = __doc__

    missing_args_message = 'Please specify input file with list of Volume pids'

    #: default verbosity level
    v_normal = 1

    def add_arguments(self, parser):
        # Positional argument for input file (required)
        parser.add_argument('input_file',
            help='Input file with a list of volume pids')
        # optional arguments
        parser.add_argument('--calculate-size',
            action='store_true',
            dest='calculate_size',
            default=False,
            help='Calculate total size of volumes and associated objects')


    def handle(self, *args, **options):
        print options
        # expects a plain text file with a list of pids,
        # one per line
        start = time.time()
        with open(options['input_file']) as infile:
            pids = [line.rstrip('\n') for line in infile]

        # if size calculation is requested, we need credentials to access
        # datastream metadata
        if options['calculate_size']:
            repo = ManagementRepository()
        # otherwise, guest access should be sufficient
        else:
            repo = Repository()

        total_size = 0
        stats = defaultdict(int)
        book_pids = set()
        for pid in pids:
            vol = repo.get_object(pid, Volume)
            if not vol.exists:
                stats['skipped'] += 1
                if options['verbosity'] > self.v_normal:
                    self.stderr.write('%s does not exist, skipping' % pid)
                continue
            if not vol.is_a_volume:
                stats['skipped'] += 1
                if options['verbosity'] > self.v_normal:
                    self.stderr.write('%s does not appear to be a Volume, skipping' % pid)
                continue

            stats['volumes'] += 1
            # output volume pid & associated book/page pids
            if options['calculate_size']:
                for ds in vol.ds_list:
                    dsobj = vol.getDatastreamObject(ds)
                    for version in dsobj.history().versions:
                        total_size += version.size


            self.stdout.write(vol.pid)
            # books are potentially repeatable
            # (could be associated with multiple volumes)
            # only output a book pid once
            if vol.book.pid not in book_pids:
                self.stdout.write(vol.book.pid)
                book_pids.add(vol.book.pid)

            if options['calculate_size']:
                total_size += self.get_object_size(vol)
                if vol.book.exists:
                    total_size += self.get_object_size(vol.book)
                elif options['verbosity'] > self.v_normal:
                    self.sdterr.write('Book %s associated with Volume %s does not exist' \
                        % (vol.book.pid, vol.pid))

            for page in vol.pages:
                stats['pages'] += 1
                self.stdout.write(page.pid)
                if options['calculate_size']:
                    if page.exists:
                        total_size += self.get_object_size(page)
                    elif options['verbosity'] > self.v_normal:
                        self.sdterr.write('Page %s associated with Volume %s does not exist' \
                            % (page.pid, vol.pid))

        # output summary after all pids are processed
        if options['verbosity'] >= self.v_normal:
            msg = 'Processed %d volume%s (skipped %d); found %d book%s and %d page%s in %.02fs.' % \
                (stats['volumes'], pluralize(stats['volumes']),
                stats['skipped'],
                len(book_pids), pluralize(book_pids),
                stats['pages'], pluralize(stats['pages']),
                time.time() - start)

            # if calculate size was requested, report
            if options['calculate_size']:
                # approximate because it does not account for size of the foxml
                msg += ' Approximate total size is %s.' % filesizeformat(total_size)
            # Using stderr here so pid list can be output to a file
            self.stderr.write(msg)

    def get_object_size(self, obj):
        # calculate approximate size for a fedora object
        # given an eulfedora digital object,
        # total up the size for all versions of all datastreams
        size = 0
        for ds in obj.ds_list:
            dsobj = obj.getDatastreamObject(ds)
            for version in dsobj.history().versions:
                size += version.size
        return size
