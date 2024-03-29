"""Factory to create Annotations for Tests"""
from random import randrange
from factory import Faker, SubFactory
from apps.users.tests.factories import UserFactory
from ...iiif.annotations.tests.factories import AnnotationFactory
from ..models import UserAnnotation

class UserAnnotationFactory(AnnotationFactory):
    """Creates UserAnnotation object for testing."""
    content = Faker('text')
    motivation = "commenting"
    owner = SubFactory(UserFactory)
    oa_annotation = {}

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        model = UserAnnotation
