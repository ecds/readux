from eulfedora.server import Repository
from django.core.management.base import BaseCommand
import shutil

from readux.books import annotate, export
from readux.books.models import Volume



class Command(BaseCommand):
    help = 'Construct web export of an annotated volume'

    def add_arguments(self, parser):
        parser.add_argument('pid', nargs='+', type=str)
        parser.add_argument('--static', action='store_true', default=False,
            help='Generate built (static) site instead of jekyll site')

    def handle(self, *args, **options):
        print args
        repo = Repository()
        for pid in options['pid']:
            vol = repo.get_object(pid, type=Volume)
            tei = annotate.annotated_tei(vol.generate_volume_tei(),
                vol.annotations())
            zipfile = export.website(vol, tei, static=options['static'])
            zipfilename = '%s-annotated-site.zip' % pid
            shutil.copyfile(zipfile.name, zipfilename)

            print 'Export for %s complete, zipfile is %s' % (vol.noid, zipfilename)
