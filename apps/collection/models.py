from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinLengthValidator
from django.core.validators import MaxLengthValidator

from toolware.utils.query import CaseInsensitiveUniqueManager


class Collection(models.Model):
    """ Collection Model """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    identification = models.CharField(
        # Translators: admin:skip
        _('COLLECTION.IDENTIFICATION'),
        max_length=255,
        unique=True,
        blank=False,
    )

    depth = models.PositiveIntegerField(
        # Translators: admin:skip
        _('COLLECTION.DEPTH'),
        default=1,
        blank=False,
    )

    context = models.CharField(
        # Translators: admin:skip
        _('COLLECTION.CONTEXT'),
        max_length=255,
        blank=True,
        null=True,
    )

    type = models.CharField(
        # Translators: admin:skip
        _('COLLECTION.TYPE'),
        max_length=60,
        blank=False,
        null=True,
    )

    label = models.CharField(
        # Translators: admin:skip
        _('COLLECTION.LABEL'),
        max_length=255,
        blank=False,
        null=True,
    )

    description = models.TextField(
        # Translators: admin:skip
        _('COLLECTION.DESCRIPTION'),
        blank=True,
        null=True,
    )

    attribution = models.TextField(
        # Translators: admin:skip
        _('COLLECTION.ATTRIBUTION'),
        blank=True,
        null=True,
    )

    logo = models.CharField(
        # Translators: admin:skip
        _('COLLECTION.LOGO'),
        max_length=255,
        blank=True,
        null=True,
    )

    children = models.ManyToManyField(
      "self",
      related_name='parents',
      symmetrical=False,
      blank=True,
    )


    # ########## Add new fields above this line #############
    objects = CaseInsensitiveUniqueManager()

    CASE_INSENSITIVE_FIELDS = [
      'context',
      'identification',
      'type',
      'label',
      'description',
      'attribution',
    ]

    class Meta:
        # Translators: admin:skip
        verbose_name = _('COLLECTION.NAME.LABEL')
        # Translators: admin:skip
        verbose_name_plural = _('COLLECTION.NAME.PLURAL')

        unique_together = ("identification", "depth")

        # permissions = (
        #     # ('add_collection', 'Can add new collection'),
        #     # ('change_collection', 'Can change all data on any collection'),
        #     # ('delete_collection', 'Can delete any collection'),
        # )

    def __str__(self):
        if self.label:
            return self.label
        return 'unknown'
