from django.test import TestCase

from eulfedora.server import Repository
from readux.collection.models import Collection

class CollectionTest(TestCase):

    def test_short_label(self):
        repo = Repository()
        coll = repo.get_object(type=Collection)
        coll.label = 'Large-Scale Digitization Initiative (LSDI) - Civil War Literature Collection'

        self.assertEqual('Civil War Literature', coll.short_label)


