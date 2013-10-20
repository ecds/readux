from django.core.management.base import NoArgsCommand

from ...utils import clean_expired_contacts


class Command(NoArgsCommand):
    help = "Delete expired contacts from the database"

    def handle_noargs(self, **options):
        """ Remove all expired contacts from the database """

        return clean_expired_contacts()





