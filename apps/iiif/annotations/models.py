"""Django models for :class:`apps.iiif.annotations`"""
from django.contrib.postgres.fields import JSONField
from django.db import models, IntegrityError
from django.conf import settings
from django.db.models import signals
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from abc import abstractmethod
from bs4 import BeautifulSoup
from guardian.shortcuts import assign_perm, get_objects_for_user, \
    get_objects_for_group, get_perms_for_model, get_perms
from guardian.models import UserObjectPermission, GroupObjectPermission
import json
import uuid
import logging

USER = get_user_model()
LOGGER = logging.getLogger(__name__)

class AnnotationQuerySet(models.QuerySet):
    'Custom :class:`~django.models.QuerySet` for :class:`Annotation`'

    def visible_to(self, user):
        """
        Return annotations the specified user is allowed to view.
        Objects are found based on view_user_annotation permission and
        per-object permissions.  Generally, superusers can view all
        annotations; users can access only their own annotations or
        those where permissions have been granted to a group they belong to.

        .. Note::
            Due to the use of :meth:`guardian.shortcuts.get_objects_for_user`,
            it is recommended to use this method must be used first; it
            does combine the existing queryset query, but it does not
            chain as querysets normally do.

        """
        qs = get_objects_for_user(user, 'view_user_annotation',
                                    Annotation)
        # combine the current queryset query, if any, with the newly
        # created queryset from django guardian
        qs.query.combine(self.query, 'AND')
        return qs

    def visible_to_group(self, group):
        """
        Return annotations the specified group is allowed to view.
        Objects are found based on view_user_annotation permission and
        per-object permissions.

        .. Note::
            Due to the use of :meth:`guardian.shortcuts.get_objects_for_user`,
            it is recommended to use this method first; it does combine
            the existing queryset query, but it does not chain as querysets
            normally do.

        """
        qs = get_objects_for_group(group, 'view_user_annotation',
                                   Annotation)
        # combine current queryset query, if any, with the newly
        # created queryset from django guardian
        qs.query.combine(self.query, 'AND')
        return qs

    def last_created_time(self):
        '''Creation time of the most recently created annotation. If
        queryset is empty, returns None.'''
        try:
            return self.values_list('created', flat=True).latest('created')
        except Annotation.DoesNotExist:
            pass

    def last_updated_time(self):
        '''Update time of the most recently created annotation. If
        queryset is empty, returns None.'''
        try:
            return self.values_list('created', flat=True).latest('created')
        except Annotation.DoesNotExist:
            pass


class AnnotationManager(models.Manager):
    '''Custom :class:`~django.models.Manager` for :class:`Annotation`.
    Returns :class:`AnnotationQuerySet` as default queryset, and exposes
    :meth:`visible_to` for convenience.'''

    def get_queryset(self):
        return AnnotationQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        'Convenience access to :meth:`AnnotationQuerySet.visible_to`'
        return self.get_queryset().visible_to(user)

    def visible_to_group(self, group):
        'Convenience access to :meth:`AnnotationQuerySet.visible_to_group`'
        return self.get_queryset().visible_to_group(group)


class AbstractAnnotation(models.Model):
    """Base class for IIIF annotations."""
    OCR = 'cnt:ContentAsText'
    TEXT = 'dctypes:Text'
    TYPE_CHOICES = (
        (OCR, 'ocr'),
        (TEXT, 'text')
    )

    COMMENTING = 'oa:commenting'
    PAINTING = 'sc:painting'
    MOTIVATION_CHOICES = (
        (COMMENTING, 'commenting'),
        (PAINTING, 'painting')
    )

    PLAIN = 'text/plain'
    HTML = 'text/html'
    FORMAT_CHOICES = (
        (PLAIN, 'plain text'),
        (HTML, 'html')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    x = models.IntegerField()
    y = models.IntegerField()
    w = models.IntegerField()
    h = models.IntegerField()
    order = models.IntegerField(default=0)
    content = models.TextField(blank=True, null=True)
    resource_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=TEXT)
    motivation = models.CharField(max_length=50, choices=MOTIVATION_CHOICES, default=PAINTING)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=PLAIN)
    canvas = models.ForeignKey('canvases.Canvas', on_delete=models.CASCADE, null=True)
    language = models.CharField(max_length=10, default='en')
    #how does owner work with permissions?
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
    oa_annotation = JSONField(default=dict, blank=False)
    # TODO: Should we keep this for annotations from Mirador, or just get rid of it?
    svg = models.TextField(blank=True, null=True)
    style = models.CharField(max_length=1000, blank=True, null=True)
    item = None

    ordering = ['order']

    def __str__(self):
        return str(self.pk)

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        abstract = True

class Annotation(AbstractAnnotation):
    """Model class for IIIF annotations."""
    def save(self, *args, **kwargs):
        if not self.content or self.content.isspace():
            raise ValidationError('Content cannot be empty')
        super(Annotation, self).save(*args, **kwargs)

    objects = AnnotationManager()

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        ordering = ['order']
        abstract = False
        permissions = (
            ('view_user_annotation', 'View annotation'),
            ('admin_annotation', 'Manage annotation'),
        )

@receiver(signals.pre_save, sender=Annotation)
def set_span_element(sender, instance, **kwargs):
    """
    Post save function to wrap the OCR content in a `<span>` to be overlayed in OpenSeadragon.

    :param sender: Class calling function
    :type sender: apps.iiif.annotations.models.Annotation
    :param instance: Annotation object
    :type instance: apps.iiif.annotations.models.Annotation
    """
    # Guard for when an OCR annotation gets re-saved.
    # Without this, it would nest the current span in a new span.
    if instance.content.startswith('<span'):
        instance.content = BeautifulSoup(instance.content, 'html.parser').span.string
    if (instance.resource_type in (sender.OCR,)) or (instance.oa_annotation['annotatedBy']['name'] == "ocr"): # pylint: disable = line-too-long
        instance.oa_annotation['annotatedBy'] = {'name': 'ocr'}
        instance.owner = USER.objects.get_or_create(username='ocr', name='OCR')[0]
        character_count = len(instance.content)
        # 1.6 is a "magic number" that seems to work pretty well ¯\_(ツ)_/¯
        font_size = instance.h / 1.6
        # Assuming a character's width is half the height. This was my first guess.
        # This should give us how long all the characters will be.
        string_width = (font_size / 2) * character_count
        letter_spacing = 0
        relative_letter_spacing = 0
        if instance.w > 0:
            # And this is what we're short.
            space_to_fill = instance.w - string_width
            # Divide up the space to fill and space the letters.
            letter_spacing = space_to_fill / character_count
            # Percent of letter spacing of overall width.
            # This is used by OpenSeadragon. OSD will update the letter spacing relative to
            # the width of the overlayed element when someone zooms in and out.
            relative_letter_spacing = letter_spacing / instance.w
        instance.content = "<span id='{pk}' class='anno-{pk}' data-letter-spacing='{p}'>{content}</span>".format(
            pk=instance.pk, content=instance.content, p=str(relative_letter_spacing)
        )
        instance.style = ".anno-{c}: {{ height: {h}px; width: {w}px; font-size: {f}px; letter-spacing: {ls}px;}}".format(
            c=(instance.pk), h=str(instance.h), w=str(instance.w), f=str(font_size), ls=str(letter_spacing)
        )



class AnnotationGroup(Group):
    """Annotation Group; extends :class:`django.contrib.auth.models.Group`.

    Intended to facilitate group permissions on annotations.
    """
    # inherits name from Group
    #: optional notes field
    notes = models.TextField(blank=True)
    #: datetime annotation was created; automatically set when added
    created = models.DateTimeField(auto_now_add=True)
    #: datetime annotation was last updated; automatically updated on save
    updated = models.DateTimeField(auto_now=True)

    def num_members(self):
        return self.user_set.count()
    num_members.short_description = '# members'

    def __repr__(self):
        return '<Annotation Group: %s>' % self.name

    @property
    def annotation_id(self):
        return 'group:%d' % self.pk
