from django.core.management.base import BaseCommand, CommandError

from readux.collection.models import Collection
from readux.collection.fixtures.collection_descriptions import descriptions
from readux.fedora import ManagementRepository


class Command(BaseCommand):
    '''Update LSDI Volume PDF ARKs to resolve to the current readux site.
Takes an optional list of pids; otherwise, looks for all Volume objects in
the configured fedora instance.'''
    help = __doc__

    def handle(self, *pids, **options):

        repo = ManagementRepository()
        # if pids are specified on command line, only process those objects
        if pids:
            objs = [repo.get_object(pid, type=Collection) for pid in pids]

        # otherwise, look for all volume objects in fedora
        else:
            objs = repo.get_objects_with_cmodel(Collection.COLLECTION_CONTENT_MODEL,
                                                type=Collection)

        for coll in objs:
            if coll.pid in descriptions:
                coll.dc.content.description = descriptions[coll.pid]
                coll.save('updating description')





