"""Django models for :class:`apps.iiif.annotations`"""

import uuid
import logging
from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from bs4 import BeautifulSoup
from ..models import IiifBase
from .choices import AnnotationSelector, AnnotationPurpose

USER = get_user_model()
LOGGER = logging.getLogger(__name__)


class AbstractAnnotation(IiifBase):
    """Base class for IIIF annotations."""

    OCR = "cnt:ContentAsText"
    TEXT = "dctypes:Text"
    TYPE_CHOICES = ((OCR, "ocr"), (TEXT, "text"))

    OA_COMMENTING = "oa:commenting"
    SC_PAINTING = "sc:painting"
    MOTIVATION_CHOICES = ((OA_COMMENTING, "commenting"), (SC_PAINTING, "painting"))

    PLAIN = "text/plain"
    HTML = "text/html"
    FORMAT_CHOICES = ((PLAIN, "plain text"), (HTML, "html"))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    w = models.IntegerField(default=0)
    h = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    content = models.TextField(blank=True, null=True, default=" ")
    resource_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=TEXT)
    # TODO: replace
    motivation = models.CharField(
        max_length=50, choices=MOTIVATION_CHOICES, default=SC_PAINTING
    )
    purpose = models.CharField(
        max_length=2, choices=AnnotationPurpose.choices, default=AnnotationPurpose("SP")
    )
    primary_selector = models.CharField(
        max_length=2,
        choices=AnnotationSelector.choices,
        default=AnnotationSelector("FR"),
    )
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=PLAIN)
    canvas = models.ForeignKey("canvases.Canvas", on_delete=models.CASCADE, null=True)
    language = models.CharField(max_length=10, default="en")
    owner = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, blank=True, null=True
    )
    oa_annotation = models.JSONField(default=dict, blank=False)
    # TODO: Should we keep this for annotations from Mirador, or just get rid of it?
    svg = models.TextField(blank=True, null=True)
    style = models.CharField(max_length=1000, blank=True, null=True)
    item = None

    ordering = ["order"]

    @property
    def content_is_html(self):
        """
        Is the content of the annotation HTML?

        :return: True if HTML tags are present in the content.
        :rtype: bool
        """
        return bool(BeautifulSoup(self.content, "html.parser").find())

    @property
    def fragment(self):
        """Web Annotation fragment selector.
        https://www.w3.org/TR/annotation-model/#fragment-selector

        Returns:
            str: FragmentSelector
        """
        return f"xywh=pixel:{self.x},{self.y},{self.w},{self.h}"

    def __str__(self):
        return str(self.pk)

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        abstract = True


class Annotation(AbstractAnnotation):
    """Model class for IIIF annotations."""

    def save(self, *args, **kwargs):
        self.set_span_element()
        super().save(*args, **kwargs)

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        ordering = ["order"]
        abstract = False

    # @receiver(signals.pre_save, sender=Annotation)
    def set_span_element(self):
        """
        Post save function to wrap the OCR content in a `<span>` to be overlaid in OpenSeadragon.

        :param sender: Class calling function
        :type sender: apps.iiif.annotations.models.Annotation
        :param instance: Annotation object
        :type instance: apps.iiif.annotations.models.Annotation
        """
        # Guard for when an OCR annotation gets re-saved.
        # Without this, it would nest the current span in a new span.
        if self.content.startswith("<span"):
            self.content = BeautifulSoup(self.content, "html.parser").span.string
        if self.resource_type in (self.OCR,):
            # pylint: disable=unsupported-assignment-operation
            self.oa_annotation["annotatedBy"] = {"name": "ocr"}
            # pylint: enable=unsupported-assignment-operation
            self.owner = USER.objects.get_or_create(username="ocr", name="OCR")[0]
            character_count = len(self.content)
            # 1.6 is a "magic number" that seems to work pretty well ¯\_(ツ)_/¯
            font_size = self.h / 1.6
            # Assuming a character's width is half the height. This was my first guess.
            # This should give us how long all the characters will be.
            string_width = (font_size / 2) * character_count
            letter_spacing = 0
            relative_letter_spacing = 0
            if self.w > 0:
                # And this is what we're short.
                space_to_fill = self.w - string_width
                # Divide up the space to fill and space the letters.
                letter_spacing = space_to_fill / character_count
                # Percent of letter spacing of overall width.
                # This is used by OpenSeadragon. OSD will update the letter spacing relative to
                # the width of the overlaid element when someone zooms in and out.
                relative_letter_spacing = letter_spacing / self.w
            # pylint: disable=line-too-long
            self.content = f"<span id='{self.pk}' class='anno-{self.pk}' data-letter-spacing='{str(relative_letter_spacing)}'>{self.content}</span>"
            self.style = f".anno-{self.pk}: {{ height: {self.h}px; width: {self.w}px; font-size: {font_size}px; letter-spacing: {letter_spacing}px;}}"
            # pylint: enable=line-too-long
