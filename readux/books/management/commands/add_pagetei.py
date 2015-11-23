# -*- coding: utf-8 -*-
from collections import defaultdict
from optparse import make_option
import os
import signal
import sys

from fuzzywuzzy import fuzz
from django.core.management.base import BaseCommand, CommandError
from progressbar import ProgressBar, Bar, Percentage, \
         ETA, Counter

from readux.collection.models import Collection
from readux.books.models import Volume, VolumeV1_0, VolumeV1_1, PageV1_0, PageV1_1
from readux.fedora import ManagementRepository

class Command(BaseCommand):
    '''Generate or update TEI facsimile XML for page-by-page OCR content,
    for the pages associated with a Readux Volume.'''
    help = __doc__
    args = '<pid> [<pid> <pid>]'

    v_normal = 1
    verbosity = None
    stats = defaultdict(int)
    repo = None
    interrupted = False

    option_list = BaseCommand.option_list + (
        make_option('--all', '-a',
            action='store_true',
            default=False,
            help='Add TEI for all volumes with pages loaded'),
        make_option('--update', '-u',
            action='store_true',
            default=False,
            help='Regenerate TEI even if already present'),
        make_option('--regenerate-ids',
            action='store_true',
            default=False,
            help='Regenerate OCR IDs even if already present (NOT RECOMMENDED)'),
        make_option('--collection', '-c',
            help='Find and process volumes that belong to the specified collection pid ' + \
            '(list of pids on the command line takes precedence over this option)'),
    )
    update_existing = True

    def handle(self, *pids, **options):
        # bind a handler for interrupt signal
        signal.signal(signal.SIGINT, self.interrupt_handler)


        self.repo = ManagementRepository()
        self.verbosity = int(options.get('verbosity', self.v_normal))
        self.update_existing = options.get('update')
        self.regenerate_ids = options.get('regenerate_ids')

        # if no pids are specified
        if not pids:

            # if collection is specified, find pids by collection
            if options['collection']:
                pids = self.pids_by_collection(options['collection'])

            # check if 'all' was specified, and if so find all volumes
            elif options['all']:
                pids = Volume.volumes_with_pages()
                if self.verbosity >= self.v_normal:
                    self.stdout.write('Found %d volumes with pages loaded' % len(pids))

            # otherwise exit with an error message
            else:
                raise CommandError('Please specify a volume pid to have TEI generated')

        for pid in pids:
            print pid
            # try volume 1.0 first, since we have more 1.0 content
            vol = self.repo.get_object(pid, type=VolumeV1_0)

            # confirm it is 1.0, then process
            if vol.has_requisite_content_models:
                if self.verbosity >= self.v_normal:
                    self.stdout.write('Processing volume %s (Volume-1.0)' % pid)
                updated = self.process_volV1_0(vol)

            # if not a 1.0, try 1.1
            else:
                vol = self.repo.get_object(pid, type=VolumeV1_1)
                # confirm it is indeed volume-1.1, then process
                if vol.has_requisite_content_models:
                    if self.verbosity >= self.v_normal:
                        self.stdout.write('Processing volume %s (Volume-1.1)' % pid)
                    updated = self.process_volV1_1(vol)

                 # if neither volume 1.0 or 1.1, error
                else:
                    self.stderr.write('%s is not a Volume-1.0 or a Volume-1.1 object' % pid)
                    continue

            if updated:
                self.stats['vol'] += 1

            # if we have received a SIGINT during this loop, stop
            # processing volumes report on what was done
            if self.interrupted:
                break

        if self.verbosity >= self.v_normal:
            if len(pids) > 1:
                self.stdout.write('Updated %d volume%s with TEI' % \
                    (self.stats['vol'], 's' if self.stats['vol'] != 1 else ''))
            self.stdout.write('Added TEI to %(added)d pages, updated %(updated)d, skipped %(skipped)d' \
                              % self.stats)

    def get_progressbar(self, total):
        # initialize & return a progressbar to track pages processed.
        # only returns when running on a tty (i.e. not redirected to a file)
        if os.isatty(sys.stderr.fileno()):
            return ProgressBar(widgets=['Pages: ', Percentage(),
                                        ' (', Counter(), ')',
                                        Bar(), ETA()],
                               maxval=total).start()

    def process_volV1_0(self, vol):
        # for page 1.0, get abbyyocr and iterate through pages in the xml
        # return number of pages updated
        updates = 0

        # if no ocr is present, error (nothing to do)
        if not vol.ocr.exists:
            self.stdout.write('No OCR datastream for Volume-1.0 %s' % vol.pid)
            return updates

        # check if tei has already been generated for this volume
        # FIXME: this check is duplicated from method process_volV1_1
        if vol.has_tei:
            # update not specified - skip
            if not self.update_existing:
                if self.verbosity > self.v_normal:
                    self.stdout.write('Volume %s already has TEI and no update requested; skipping.' \
                      % vol.pid)
                return
            # update requested; report and continue
            elif self.verbosity > self.v_normal:
                self.stdout.write('Updating existing TEI for Volume %s' \
                      % vol.pid)

        # if volume does not yet have ids in the ocr, add them
        # OR if id-regeneration is requested
        if self.regenerate_ids or not vol.ocr_has_ids:
            if self.verbosity >= self.v_normal:
                self.stdout.write('Adding ids to %s OCR' % vol.pid)
            added = vol.add_ocr_ids(regenerate_ids=self.regenerate_ids)
            # if for some reason adding ids failed, bail out
            if not added:
                self.stderr.write('Error adding ids to OCR for %s' % vol.pid)
                return
            vol.save('Adding ids to OCR')

        ocr_pages = vol.ocr.content.pages
        pbar = self.get_progressbar(len(vol.pages))

        # NOTE: this *does* depend on pages loaded in order
        # (and no missing pages?)
        # index into ocr pages list, to match page objects with ocr
        index = vol.start_page - 1 if vol.start_page is not None else 0

        for p in vol.pages:
            # FIXME: can volume return page as the appropriate kind of page object?
            page = self.repo.get_object(p.pid, type=PageV1_0)
            if self.verbosity > self.v_normal:
                self.stdout.write('%s page %s' % (page.pid, page.page_order))

            # NOTE: some pages have no tei, but since the abbyy ocr
            # includes page content for every page, we're going to
            # generate TEI for those pages too;
            # includes page information, and may include illustration blocks.

            # For the first few pages, do some checking that text content
            # matches, to ensure we don't load TEI for the wrong page.
            # Using fuzzy matching here because sometimes one version
            # contains control characters not present in the other.
            # For now, if we get a mismatch, bail out.  Eventually we may
            # want to add logic to detect the correct ocr page index.
            if index < 10:
                page_text = normalize_ws(unicode(page.text.content.read(),
                    'utf-8', 'replace'))
                ocr_text = normalize_ws(unicode(ocr_pages[index]))

                # NOTE: if there are unicode discrepancies, we may want to
                # add generalized unicode cleanup or convert specific characters, e.g
                # ocr_text = unicodedata.normalize('NFKD', ocr_text).encode('ascii','ignore')
                # ocr_text = ocr_text.replace(u'¬', u'-')

                # if page has text, check for at least 95% token match
                # NOTE: using token set match gives better results than
                # straight fuzz.ratio, where minor differences like
                # ¬ vs - results in a very low score
                if (page_text and ocr_text) and \
                  fuzz.token_set_ratio(page_text, ocr_text) < 95:
                    self.stderr.write('Error: page text for %d does not seem to match OCR' % index)
                    # TBD: should we keep processing even if we get a mismatch?
                    break

            if page.tei.exists:
                verb = 'updated'
                self.stats['updated'] += 1
            else:
                verb = 'added'
                self.stats['added'] += 1
            # generate TEI and add or update the TEI datastream with the contents
            page.update_tei(ocr_pages[index])
            page.save('%s tei facsimile' % verb)
            updates += 1

            if pbar:
                pbar.update(updates)

            index += 1

        if pbar:
            pbar.finish()

        return updates


    def process_volV1_1(self, vol):
        # load tei for vol 1.1 / pages 1.1

        # check if tei has already been generated for this volume
        if vol.has_tei:
            # update not specified - skip
            if not self.update_existing:
                if self.verbosity > self.v_normal:
                    self.stdout.write('Volume %s already has TEI and no update requested; skipping.' \
                      % vol.pid)
                return
            # update requested; report and continue
            elif self.verbosity > self.v_normal:
                self.stdout.write('Updating existing TEI for Volume %s' \
                      % vol.pid)

        updates = 0
        pbar = self.get_progressbar(len(vol.pages))

        for p in vol.pages:

            # FIXME: can volume return page as the appropriate kind of page object?
            page = self.repo.get_object(p.pid, type=PageV1_1)
            if self.verbosity > self.v_normal:
                self.stdout.write('%s page %s' % (page.pid, page.page_order))

            # for page 1.1, ocr is on the page object
            if not page.ocr.exists:
                if self.verbosity >= self.v_normal:
                    self.stdout.write('No ocr content for %s (page %d); skipping' \
                        % (page.pid, page.page_order))
                self.stats['skipped'] += 1
                continue

            # if page does not yet have ids in the ocr, add them
            # OR if id-regeneration is requested
            if self.regenerate_ids or not page.ocr_has_ids:
                if self.verbosity > self.v_normal:
                    self.stdout.write('Adding ids to %s OCR' % page.pid)
                if not page.add_ocr_ids(regenerate_ids=self.regenerate_ids):
                    self.stdout.write('Failed to add OCR ids to %s' % page.pid)
                page.save('Adding ids to OCR')

            if page.tei.exists:
                verb = 'updated'
                self.stats['updated'] += 1
            else:
                verb = 'added'
                self.stats['added'] += 1
            # generate TEI and add or update the TEI datastream with the contents
            page.update_tei()
            page.save('%s tei facsimile' % verb)

            updates += 1
            if pbar:
                pbar.update(updates)

        if pbar:
            pbar.finish()

        return updates

    def pids_by_collection(self, pid):
        # NOTE: this method is based on the one in BasePageImport,
        # but returns a list of pids instead of a list of Volumes
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
        pids = []
        for book in coll.book_set:
            pids.extend([v.pid for v in book.volume_set])

        return pids


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
            # set interrupt flag so main loop knows to quit
            self.interrupted = True
            print >> self.stdout, \
                  '\n\nScript will exit after all pages for the current volume are processed.' + \
                  '\n(Ctrl-C / Interrupt again to quit now)'


def normalize_ws(val):
    # normalize whitespace and remove control characters
    val = u' '.join(val.split())  # split on whitespace and rejoin
    return u''.join([c for c in val if ord(c) > 31 or ord(c) == 9])
