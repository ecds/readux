from factory import DjangoModelFactory, Faker, post_generation, RelatedFactory
from apps.iiif.manifests.models import Manifest
from apps.iiif.canvases.tests.factories import CanvasFactory
import random

class ManifestFactory(DjangoModelFactory):
    pid = str(random.randrange(2000, 5000))
    label = Faker("name")
    canvase = RelatedFactory(CanvasFactory, 'manifest')
    
    # @post_generation
    # def add_canvases(self, create, how_many, **kwargs):
    #     at_least = 5
    #     if not create:
    #         return
    #     for n in range(how_many or at_least):
    #         # CanvasFactory.create(manifest=self)
    #         self.canvase = RelatedFactory(CanvasFactory, 'manifest')

    class Meta:
        model = Manifest