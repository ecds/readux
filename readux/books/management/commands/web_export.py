from eulfedora.server import Repository
from eulxml.xmlmap import load_xmlobject_from_file
from django.core.management.base import BaseCommand
import shutil

from readux.books import annotate, export
from readux.books.models import Volume
from readux.books.tei import Facsimile


class Command(BaseCommand):
    help = 'Construct web export of an annotated volume'

    def add_arguments(self, parser):
        parser.add_argument('pid', nargs='+', type=str)
        parser.add_argument('--static', action='store_true', default=False,
            help='Generate built (static) site instead of jekyll site')
        parser.add_argument('--tei',
            help='Use the specified TEI file instead of generating it')

    def handle(self, *args, **options):
        repo = Repository()
        for pid in options['pid']:
            vol = repo.get_object(pid, type=Volume)
            if options['tei']:
                tei = load_xmlobject_from_file(options['tei'], Facsimile)
            else:
                tei = annotate.annotated_tei(vol.generate_volume_tei(),
                    vol.annotations())
            zipfile = export.website(vol, tei, static=options['static'])
            zipfilename = '%s-annotated-site.zip' % vol.noid
            shutil.copyfile(zipfile.name, zipfilename)

            print 'Export for %s complete, zipfile is %s' % (vol.noid, zipfilename)
