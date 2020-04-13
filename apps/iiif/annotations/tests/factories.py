from factory import DjangoModelFactory, Faker, SubFactory
from apps.iiif.annotations.models import Annotation
import random

class AnnotationFactory(DjangoModelFactory):
    # pid = str(random.randrange(2000, 5000))
    # label = Faker("name")
    # height = random.randrange(200, 500)
    # width = random.randrange(200, 500)
    # position = random.randrange(5)
    # IIIF_IMAGE_SERVER_BASE = SubFactory(IServerFactory)

    class Meta:
        model = Annotation