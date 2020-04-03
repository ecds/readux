from factory import DjangoModelFactory, Faker, post_generation
from .models import Canvas
import random

class CanvasFactory(DjangoModelFactory):
    pid = str(random.randrange(2000, 5000))
    label = Faker("name")
    height = random.randrange(200, 500)
    width = random.randrange(200, 500)
    position = random.randrange(5)

    class Meta:
        model = Canvas