'''
This manage.py command should be used for loading cover images into Readux.
Covers must be loaded before full page-image content can be loaded for a Volume.

This script requires access to the Digitization Workflow application; the REST
endpoint should be configured in localsettings via **DIGITIZATION_WORKFLOW_API**.
Running this script also requires that the image paths referenced in the
Digitization Workflow application be mounted locally at the same path, in order
to access and identify page image content.

Because identifying cover images and loading them into Fedora can be a slow
process, if you want to load more covers at once you may find it useful to
run the script in collection mode (load covers for a specific collection), e.g.::

    python manage.py import_covers -c emory-control:LSDI-RegimentalHistories

Then you can run multiple versions of the script in parallel, so that multiple
collections can be loaded at once.  It is recommended to use the ``screen`` command
to manage multiple instances of the script running on a remote server, both to
avoid the script being interrupted by a connection error, and so you can easily
check on and manage multiple instances of the script running at once.

.. Note::

    If the script detects that a Volume already has a cover image associated,
    it will simply skip it and not make any changes or re-upload a cover, *unless*
    the ``--update`` option is specified, in which case it will check to see if
    the existing cover needs to be updated.  This means it is entirely safe to re-run
    the import on a collection that has been partially imported or even all
    Volumes in order to pick up covers for Volumes that were missed previously.

If a cover has been detected and assigned incorrectly, use the ``--update`` command
with the specified pid or collection to try detecting the cover and updating the
record in Fedora.  However, if neither the data in the Digitization Workflow nor
the cover detection logic in readux have been changed since the last run, it is
unlikely a different cover image will be detected.

This script does have an interrupt handler configured, so if you need to stop
the import while it is in progress (e.g., if you know the Fedora Repository
needs to be restarted), first try a single control-c which will attempt to exit
cleanly after processing the current volume, and should report on what was
completed before the interruption.

----

'''
import logging
from optparse import make_option
import os
import signal
import sys

from django.core.management.base import BaseCommand
from progressbar import ProgressBar, Bar, Percentage, \
         ETA, Counter

from readux.books.models import VolumeV1_0
from readux.books.management.page_import import BasePageImport


logger = logging.getLogger(__name__)


class Command(BasePageImport):
    '''Identify and ingest cover images for Volume objects in Fedora.
Takes an optional list of pids; otherwise, looks for all Volume objects in
the configured fedora instance, or in a single collection specified by pid.'''
    help = __doc__
    args = '<pid> [<pid> [<pid>]]'

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n',
            action='store_true',
            default=False,
            help='Don\'t make any changes; just report on what would be done'),
        make_option('--collection', '-c',
            help='Find and process volumes that belong to the specified collection pid ' + \
            '(list of pids on the command line takes precedence over this option)'),
        make_option('--update', '-u',
            action='store_true',
            default=False,
            help='Update volumes even if they already have a cover ' + \
            '(use current cover detection logic and update the existing cover if different)'),
        )

    #: interruption flag set by :meth:`interrupt_handler`
    interrupted = False

    #: number of objects to be processed; set in :meth:`handle`
    total = None

    def handle(self, *pids, **options):
        # bind a handler for interrupt signal
        signal.signal(signal.SIGINT, self.interrupt_handler)

        self.setup(**options)
        # is update logic requested?
        update = options.get('update', False)

        # if pids are specified on command line, only process those objects
        # (takes precedence over collection)
        if pids:
            objs = [self.repo.get_object(pid, type=VolumeV1_0) for pid in pids]

        # if collection is specified, find pids by collection
        elif options['collection']:
            objs = self.pids_by_collection(options['collection'])

        # otherwise, look for all volume objects in fedora
        else:
            objs = self.repo.get_objects_with_cmodel(VolumeV1_0.VOLUME_CONTENT_MODEL,
                                                type=Volume)

        self.total = len(objs)

        pbar = None
        # NOTE: possibly should not be displayed when verbosity is 0, also?
        if self.total >= 5 and os.isatty(sys.stderr.fileno()):
            # init progress bar if we're indexing enough items to warrant it
            pbar = ProgressBar(widgets=['Volumes: ', Percentage(),
                                        ' (', Counter(), ')',
                                        Bar(),
                                        ETA()], maxval=self.total).start()

        for vol in objs:
            # if a SIGINT was received while processing the last volume, stop now
            if self.interrupted:
                break

            if pbar:  # should this be after incrementd?
                pbar.update(self.stats['vols'])

            self.stats['vols'] += 1
            # if object does not exist or cannot be accessed in fedora, skip it
            if not self.is_usable_volume(vol):
                continue

            # if volume already has a cover, don't re-ingest
            if vol.primary_image:
                # special case for now: don't try to update volumes that have
                # already had pages loaded (could mess up page order)
                if update and vol.page_count > 1:
                    self.stdout.write('Update was requested but %s has pages loaded; update is not supported' % \
                                      vol.pid)
                    self.stats['skipped'] += 1
                    continue

                if self.verbosity >= self.v_normal:
                    self.stdout.write('%s already has a cover image %s' % \
                        (vol.pid, vol.primary_image.pid))

                # otherwise, skip unless update was requested
                if not update:
                    self.stats['skipped'] += 1
                    continue

            images, vol_info = self.find_page_images(vol)
            # if either images or volume info were not found, skip
            if not images or not vol_info:
                self.stats['skipped'] += 1   # or error?
                continue

            # cover detection (currently first non-blank page)
            coverfile, coverindex = self.identify_cover(images, vol_info.pdf)

            # if a non-blank page was not found in the first 5 pages,
            # report as an error and skip this volume
            if coverindex is None:
                if self.verbosity >= self.v_normal:
                    self.stdout.write('Error: could not identify cover page in first %d images; skipping' % \
                                      self.cover_range)
                continue        # skip to next volume

            # Also leverage cover-detection/title page logic to store the page index
            # where the PDF should be opened by default
            if not vol.start_page or (update and vol.start_page != coverindex + 1):
                # needs to be 1-based page index
                vol.start_page = coverindex + 1
                vol.save('setting PDF start page')
                logger.debug('Setting %s start page to %s', vol.pid, coverindex + 1)

            # if volume already has a primary image and update was requested,
            # update the existing image object if there is any change
            if vol.primary_image and update:
                self.ingest_page(coverfile, vol, vol_info, cover=True,
                                 update=True, page=vol.primary_image)
            else:
                # create the page image object and associate with volume
                self.ingest_page(coverfile, vol, vol_info, cover=True)


        if pbar and not self.interrupted:
            pbar.finish()

        if self.verbosity >= self.v_normal:
            self.stdout.write('\n%(vols)d volume(s); %(errors)d error(s), %(skipped)d skipped, %(updated)d updated' % \
                self.stats)

    def interrupt_handler(self, signum, frame):
        '''Gracefully handle a SIGINT, if possible.  Reports status,
        sets a flag so main script loop can exit cleanly, and restores
        the default SIGINT behavior, so that a second interrupt will
        stop the script.
        '''
        if signum == signal.SIGINT:
            # restore default signal handler so a second SIGINT can be used to quit
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            # set interrupt flag so main loop knows to quit at a reasonable time
            self.interrupted = True
            msg = '''\nProcessing %d of %d volumes; script will exit after current volume.
(Ctrl-C / Interrupt again to quit immediately)'''

            print >> self.stdout, msg % (self.stats['vols'], self.total)
