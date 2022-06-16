from time import time
from uuid import uuid4, UUID
from dirtyfields import DirtyFieldsMixin
from django.db import models
from django.utils import timezone
from modelcluster.models import ClusterableModel
from apps.utils.noid import encode_noid

class IiifBase(DirtyFieldsMixin, ClusterableModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=True)
    pid = models.CharField(
        max_length=255,
        default=encode_noid,
        blank=False,
        help_text="Unique ID. Do not use _'s or spaces in the pid."
    )
    label = models.CharField(max_length=1000, default='')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    @property
    def created_at_iso(self):
        return self.__js_isoformat(self.created_at)

    @property
    def modified_at_iso(self):
        return self.__js_isoformat(self.modified_at)

    def save(self, *args, **kwargs): # pylint: disable = arguments-differ
        self.clean_pid()

        if self._state.adding:
            dup_pids = self.__class__.objects.filter(pid=self.pid)
            if dup_pids.exists() or not self.pid:
                self.dup_pid = self.pid
                self.pid = encode_noid()


        super().save(*args, **kwargs)

    @staticmethod
    def __js_isoformat(date):
        return date.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def clean_pid(self):
        """ Cantaloupe is generally configured substitute a slash (/)
        with an underscore (_) for the file path of the images. """
        self.pid = self.pid.replace('_', '-')


    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        abstract = True
