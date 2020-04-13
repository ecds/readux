from factory import DjangoModelFactory, Faker, LazyAttribute
from factory.django import ImageField
from apps.iiif.kollections.models import Collection
from django.core.files.base import ContentFile
import random

class CollectionFactory(DjangoModelFactory):
    pid = str(random.randrange(2000, 5000))
    label = Faker("name")
    original = LazyAttribute(
        lambda _: ContentFile(
            ImageField()._make_data(
                {'width': 1024, 'height': 768}
            ), 'example.jpg'
        )
    )

    class Meta:
        model = Collection