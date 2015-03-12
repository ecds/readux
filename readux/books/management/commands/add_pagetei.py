from collections import defaultdict
from django.core.management.base import BaseCommand

from readux.books.models import VolumeV1_1, PageV1_1
from readux.fedora import ManagementRepository

class Command(BaseCommand):
    '''generate
'''
    help = __doc__
    args = '<pid>'

    v_normal = 1

    def handle(self, *pids, **options):
        repo = ManagementRepository()
        verbosity = int(options.get('verbosity', self.v_normal))

        # TODO: how to handle volume v1.0 vs 1.1 ?
        if pids:
            # single volume only for now
            vol = repo.get_object(pids[0], type=VolumeV1_1)

        # currently pages are not returned in order, but that shouldn't
        # matter much for our purposes, since ocr is on the page object
        # TODO: update eulfedora to use sparql so related objects can be sorted
        stats = defaultdict(int)
        for p in vol.pages:
            # FIXME: can volume return page as the appropriate kind of page object?
            page = repo.get_object(p.pid, type=PageV1_1)
            print '%s page no %s' % (page.pid, page.page_order)
            if not page.ocr.exists:
                if verbosity >= self.v_normal:
                    self.stdout.write('No ocr content for %s (page %d); skipping' \
                        % (page.pid, page.page_order))
                stats['skipped'] += 1
                continue
            if page.tei.exists:
                verb = 'updated'
                stats['updated'] += 1
            else:
                verb = 'added'
                stats['added'] += 1
            # generate TEI and add or update the TEI datastream with the contents
            page.update_tei()
            page.save('%s tei facsimile' % verb)
            # get xml from ocr datastream
            # run xslt to generate tei
            # add tei datastream and save object
            # TODO: keep track of and report on # added, updated

        if verbosity >= self.v_normal:
            self.stdout.write('Added TEI to %(added)d pages, updated %(updated)d, skipped %(skipped)d' \
                              % stats)