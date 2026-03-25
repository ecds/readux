"""Factory to create Annotations for Tests"""

from factory import Faker, SubFactory
from apps.iiif.annotations.models import Annotation
from apps.iiif.annotations.choices import AnnotationPurpose
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.users.tests.factories import UserFactory
from ...iiif.annotations.tests.factories import AnnotationFactory
from ..models import UserAnnotation


class UserAnnotationFactory(AnnotationFactory):
    """Creates UserAnnotation object for testing."""

    content = Faker("text")
    motivation = Annotation.OA_COMMENTING
    owner = SubFactory(UserFactory)
    oa_annotation = {}
    resource_type = UserAnnotation.TEXT
    purpose = AnnotationPurpose("CM")
    canvas = SubFactory(CanvasFactory)

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = UserAnnotation
