from eulfedora.server import Repository
from django.core.management.base import BaseCommand

from readux.books import export
from readux.books.models import Volume



class Command(BaseCommand):
    help = 'Construct web export of an annotated volume'

    def add_arguments(self, parser):
        parser.add_argument('pid', nargs='+', type=str)

    def handle(self, *args, **options):
        repo = Repository()
        for pid in options['pid']:
            vol = repo.get_object('emory:4ckk0', type=Volume)
            export.static_website(vol)
