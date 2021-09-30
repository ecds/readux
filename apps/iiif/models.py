from time import time
from uuid import uuid4, UUID
from dirtyfields import DirtyFieldsMixin
from django.db import models, IntegrityError
from modelcluster.models import ClusterableModel
from apps.utils.noid import encode_noid

class IiifBase(DirtyFieldsMixin, ClusterableModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=True)
    pid = models.CharField(
        max_length=255,
        default=encode_noid(int(time())),
        blank=False,
        help_text="Unique ID. Do not use _'s or spaces in the pid."
    )
    label = models.CharField(max_length=255)

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        abstract = True
