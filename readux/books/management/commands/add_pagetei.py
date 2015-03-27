from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError

from readux.books.models import VolumeV1_0, VolumeV1_1, PageV1_0, PageV1_1
from readux.fedora import ManagementRepository

class Command(BaseCommand):
    '''Generate or update TEI facsimile XML for page-by-page OCR content.'''
    help = __doc__
    args = '<pid> [<pid> <pid>]'

    v_normal = 1
    verbosity = None
    stats = defaultdict(int)
    repo = None

    def handle(self, *pids, **options):
        self.repo = ManagementRepository()
        self.verbosity = int(options.get('verbosity', self.v_normal))

        # if no pids are specified, exit with an error message
        if not pids:
            raise CommandError('Please specify a volume pid to have TEI generated')

        for pid in pids:
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

        if self.verbosity >= self.v_normal:
            if len(pids) > 1:
                self.stdout.write('Updated %(vol)d volumes with TEI' % self.stats)
            self.stdout.write('Added TEI to %(added)d pages, updated %(updated)d, skipped %(skipped)d' \
                              % self.stats)

    def process_volV1_0(self, vol):
        # for page 1.0, get abbyyocr and iterate through pages in the xml
        # return number of pages updated
        updates = 0

        # if no ocr is present, error (nothing to do)
        if not vol.ocr.exists:
            self.stdout.write('No OCR datastream for Volume-1.0 %s' % vol.pid)
            return updates

        ocr_pages = vol.ocr.content.pages

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
            # generate TEI for those pages too
            # includes page information, and may include illustration blocks

            # NOTE: could do some simple text content comparison to check that
            # the ocr index is correct...
            # e.g. do a whitespace-insensitive check of starting n characters
            # page.text.content.read()
            # unicode(ocr_pages[index])

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

            index += 1

        return updates


    def process_volV1_1(self, vol):
        # load tei for vol 1.1 / pages 1.1
        updates = 0

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

        return updates
