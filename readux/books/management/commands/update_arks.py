from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from optparse import make_option
from collections import defaultdict

from eulfedora.server import Repository
from pidservices.clients import is_ark, parse_ark
from pidservices.djangowrapper.shortcuts import DjangoPidmanRestClient

from readux.books.models import Volume
from readux.utils import absolutize_url

class Command(BaseCommand):
    '''Update LSDI Volume ARKs to resolve to the current readux site.
Takes an optional list of pids; otherwise, looks for all Volume objects in
the configured fedora instance.  Updates both unqualified and PDF ARK targets.

NOTE: this script should be run after covers have been imported, so PDF start
page information (if any) can be taken advantage when generating PDF target urls.
'''
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

        repo = Repository()
        try:
            pidman = DjangoPidmanRestClient()
        except Exception as err:
            # error if pid manager config options not in localsettings
            raise CommandError(err)

        # if pids are specified on command line, only process those objects
        if pids:
            objs = [repo.get_object(pid, type=Volume) for pid in pids]

        # otherwise, look for all volume objects in fedora
        else:
            objs = repo.get_objects_with_cmodel(Volume.VOLUME_CONTENT_MODEL,
                                                type=Volume)

        stats = defaultdict(int)
        for obj in objs:
            stats['objs'] += 1
            if is_ark(obj.dc.content.identifier):
                parsed_ark = parse_ark(obj.dc.content.identifier)
                noid = parsed_ark['noid']
                try:
                    ark_info = pidman.get_ark(noid)
                except Exception as err:
                    # requested ARK is not in the configured pid manager
                    # (this should ONLY happen in dev/QA)
                    if verbosity >= self.v_normal:
                        if '404: NOT FOUND' in str(err):
                            msg = 'not found'
                            self.stdout.write('Error retriving ARK information for %s: Not Found' % obj.pid)
                        else:
                            self.stdout.write('Error retriving ARK information for %s' % obj.pid)
                    stats['skipped'] += 1
                    continue

                # update unqualified ark to resolve to readux volume landing page
                if not dry_run:
                    pidman.update_ark_target(noid,
                        target_uri=self.volume_url(obj),
                        active=True)

                # we expected a qualified ARK target for the PDF
                qual = 'PDF'
                # list of all qualifiers for targets associated with this ARK
                targets = [t.get('qualifier', None) for t in ark_info['targets']]
                # only update if this ARK already has a qualified PDF ARK
                if qual in targets:
                    stats['updated'] += 1   # count as updated in dry run mode (would be updated)
                    if not dry_run:
                        pidman.update_ark_target(noid, qual,
                            target_uri=self.pdf_url(obj),
                            active=True)
                        # FIXME: catch possible exceptions here?

        # output summary
        if verbosity >= self.v_normal:
            msg = 'Processed %(objs)d object%%s; skipped %(skipped)d,%%s updated %(updated)d' % stats
            msg = msg % ('s' if stats['objs'] != 1 else '', ' would have' if dry_run else '')
            self.stdout.write(msg)

    def pdf_url(self, obj):
        # generate an absolute url to the pdf for a volume object
        return absolutize_url(obj.pdf_url())

    def volume_url(self, obj):
        # generate an absolute url to the pdf for a volume object
        return absolutize_url(reverse('books:volume', kwargs={'pid': obj.pid}))
