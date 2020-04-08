from factory import DjangoModelFactory, Faker, SubFactory
from apps.iiif.canvases.models import Canvas, IServer
import random

class IServerFactory(DjangoModelFactory):
    IIIF_IMAGE_SERVER_BASE = 'http://images.ecds.emory.edu'
    class Meta:
        model = IServer

class CanvasFactory(DjangoModelFactory):
    pid = str(random.randrange(2000, 5000))
    label = Faker("name")
    height = random.randrange(200, 500)
    width = random.randrange(200, 500)
    position = random.randrange(5)
    IIIF_IMAGE_SERVER_BASE = SubFactory(IServerFactory)

    class Meta:
        model = Canvas