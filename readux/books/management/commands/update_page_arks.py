from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from eulfedora.server import Repository, RequestFailed
from pidservices.djangowrapper.shortcuts import DjangoPidmanRestClient
from progressbar import ProgressBar, Bar, Percentage, \
         ETA, Counter
import requests
import signal

from readux.books.models import Page

class Command(BaseCommand):
    '''Update Readux Page ARK default target from old-style page URLs
(Release 1) to the new format of page urls in Release 1.3.
'''
    help = __doc__

    v_normal = 1

    interrupted = False

    def handle(self, *pids, **options):
        # bind a handler for interrupt signal
        signal.signal(signal.SIGINT, self.interrupt_handler)

        verbosity = int(options.get('verbosity', self.v_normal))

        repo = Repository()
        try:
            pidman = DjangoPidmanRestClient()
        except Exception as err:
            # error if pid manager config options not in localsettings
            raise CommandError(err)

        old_page_target = '%s/books/pages/' % Site.objects.get_current().domain
        search_args = {'type':'ark', 'target': old_page_target, 'count': 100}
        results = pidman.search_pids(**search_args)
        total = results['results_count']
        if verbosity >= self.v_normal:
            print 'Found %d total page ARKs with targets to be updated' % total

        pbar = ProgressBar(widgets=[Percentage(),
            ' (', Counter(), ')',
            Bar(),
            ETA()],
            maxval=total).start()

        stats = defaultdict(int)
        self.processed = set()
        # NOTE: this could be a very large list in production
        # but otherwise, the list changes as we process updates
        # and we end up skipping results...
        arks_to_change = list(self.get_search_results(results, pidman, search_args))
        for ark in arks_to_change:
            self.processed.add(ark['pid'])
            # get fedora pid from target uri
            target_uri = ark['targets'][0]['target_uri']
            baseurl, pid = target_uri.rstrip('/').rsplit('/', 1)
            try:
                page = repo.get_object(pid, type=Page)
                # this should probably only happen in dev/qa
                if not page.exists:
                    if verbosity > self.v_normal:
                        self.stderr.write('Page %s does not exist' % pid)
                    stats['notfound'] += 1
                else:
                    # check if volume exists?
                    pidman.update_ark_target(ark['pid'], target_uri=page.absolute_url)
                    stats['updated'] += 1
            except RequestFailed as rf:
                print 'Error accessing %s: %s' % (pid, rf)
                stats['error'] += 1

            pbar.update(len(self.processed))
            if self.interrupted:
                break

        if not self.interrupted:
            pbar.finish()
        # summarize
        self.stderr.write('Updated %(updated)d, %(error)d error(s), %(notfound)d not found' \
            % stats)

    def get_search_results(self, search_results, pidman, search_args):
        # generator to page through pidman search results and
        # return the results
        for res in search_results['results']:
            if res['pid'] not in self.processed:
                yield res
        if 'next_page_link' in search_results and \
          search_results['next_page_link'] is not None:
            next_page = int(search_results['current_page_number']) + 1
            try:
                results = pidman.search_pids(page=next_page, **search_args)
                for res in self.get_search_results(results, pidman, search_args):
                    yield res
            except requests.exceptions.HTTPError:
                # 404 should mean we hit the end of the search results
                pass


    def interrupt_handler(self, signum, frame):
        '''Gracefully handle a SIGINT.  Stop and report what was done.'''
        if signum == signal.SIGINT:
            # restore default signal handler so a second SIGINT can be used to quit
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            # set interrupt flag so main loop knows to quit
            self.interrupted = True


