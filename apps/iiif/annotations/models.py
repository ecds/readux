"""Django models for :class:`apps.iiif.annotations`"""
from django.contrib.postgres.fields import JSONField
from django.db import models, IntegrityError
from django.conf import settings
from django.db.models import signals
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from abc import abstractmethod
from bs4 import BeautifulSoup
import json
import uuid
import logging

USER = get_user_model()
LOGGER = logging.getLogger(__name__)

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
    content = models.TextField(blank=True, null=True, default=' ')
    resource_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=TEXT)
    motivation = models.CharField(max_length=50, choices=MOTIVATION_CHOICES, default=PAINTING)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=PLAIN)
    canvas = models.ForeignKey('canvases.Canvas', on_delete=models.CASCADE, null=True)
    language = models.CharField(max_length=10, default='en')
    #how does owner work with permissions
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
        # if not self.content or self.content.isspace():
            # raise ValidationError('Content cannot be empty')
            # self.content = '  '
        super(Annotation, self).save(*args, **kwargs)


    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        ordering = ['order']
        abstract = False

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
