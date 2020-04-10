"""Django models representing IIIF canvases and IIIF image server info."""
import uuid
from bs4 import BeautifulSoup
import config.settings.local as settings
from django.apps import apps
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from ..manifests.models import Manifest
from ..annotations.models import Annotation
from . import services

USER = get_user_model()

# TODO: move this to the manifest model
class IServer(models.Model):
    """Django model for IIIF image server info. Each canvas has one IServer"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    IIIF_IMAGE_SERVER_BASE = models.CharField(
        max_length=255,
        default=settings.IIIF_IMAGE_SERVER_BASE
    )

    def __str__(self):
        return "%s" % (self.IIIF_IMAGE_SERVER_BASE)

class Canvas(models.Model):
    """Django model for IIIF Canvas objects."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    pid = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.CASCADE)
    position = models.IntegerField()
    height = models.IntegerField(default=0)
    width = models.IntegerField(default=0)
    # TODO: make this lowercase
    IIIF_IMAGE_SERVER_BASE = models.ForeignKey(IServer, on_delete=models.CASCADE, null=True)
    is_starting_page = models.BooleanField(default=False)
    preferred_ocr = (
        ('word', 'word'),
        ('line', 'line'),
        ('both', 'both')
    )
    # TODO: move this to the mainfest level.
    default_ocr = models.CharField(max_length=30, choices=preferred_ocr, default="word")

    @property
    def identifier(self):
        """Concatenated property to represent IIIF identifier."""
        return '{h}/iiif/{m}/canvas/{c}'.format(
            h=settings.HOSTNAME,
            m=self.manifest.pid,
            c=self.pid
        )

    @property
    def service_id(self):
        """Concatenated property to represent IIIF service id."""
        return '{h}/{c}'.format(
            h=self.IIIF_IMAGE_SERVER_BASE,
            c=self.pid
        )

    @property
    def anno_id(self):
        """Concatenated property to represent IIIF annotation links."""
        return '{h}/iiif/{m}/annotation/{c}'.format(
            h=settings.HOSTNAME,
            m=self.manifest.pid,
            c=self.pid
        )

    @property
    def image_info(self):
        """Convenience property for the canvas' IIIF info json URL."""
        return services.get_canvas_info(self)

    @property
    def thumbnail(self):
        """Concatenated property to represent IIIF thumbnail link."""
        return '{h}/{c}/full/200,/0/default.jpg'.format(
            h=self.IIIF_IMAGE_SERVER_BASE,
            c=self.pid
        )

    @property
    def social_media(self):
        """Concatenated property to represent IIIF image link for use in Open Graph metadata."""
        return '{h}/{c}/full/600,/0/default.jpg'.format(
            h=self.IIIF_IMAGE_SERVER_BASE,
            c=self.pid
        )

    @property
    def twitter_media1(self):
        """Concatenated property for twitter cards and Open Graph metadata."""
        # TODO: shouldn't this use `self.IIIF_IMAGE_SERVER_BASE`
        return 'http://images.readux.ecds.emory.edu/cantaloupe/iiif/2/{c}/full/600,/0/default.jpg'.format(
            c=self.pid
        )

    @property
    def twitter_media2(self):
        """Concatenated property for twitter cards and Open Graph metadata."""
        return '{h}/{c}/full/600,/0/default.jpg'.format(
            h=self.IIIF_IMAGE_SERVER_BASE,
            c=self.pid
        )

    @property
    def uri(self):
        """Concatenated property to represent IIIF manifest URI"""
        return '{h}/iiif/{m}/'.format(
            h=settings.HOSTNAME,
            m=self.manifest.pid
        )

    @property
    def thumbnail_crop_landscape(self):
        """Concatenated property for cropped landscape URI"""
        if self.height > self.width:
            # portrait
            return '{h}/{c}/full/,250/0/default.jpg'.format(
                h=self.IIIF_IMAGE_SERVER_BASE,
                c=self.pid
            )
        # landscape
        return '{h}/{c}/pct:25,0,50,100/,250/0/default.jpg'.format(
            h=self.IIIF_IMAGE_SERVER_BASE,
            c=self.pid
        )

    @property
    def thumbnail_crop_tallwide(self):
        """Concatenated property for cropped tallwide URI"""
        if self.height > self.width:
            # portrait
            return '{h}/{c}/pct:5,5,90,90/,250/0/default.jpg'.format(
                h=self.IIIF_IMAGE_SERVER_BASE,
                c=self.pid
            )
        # landscape
        return "%s/%s/pct:5,5,90,90/250,/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def thumbnail_crop_volume(self):
        """Concatenated property for cropped volume URI"""
        if self.height > self.width:
            # portrait
            return '{h}/{c}/pct:15,15,70,70/,600/0/default.jpg'.format(
                h=self.IIIF_IMAGE_SERVER_BASE,
                c=self.pid
            )
        # landscape
        return '{h}/{c}/pct:25,15,50,85/,600/0/default.jpg'.format(
            h=self.IIIF_IMAGE_SERVER_BASE,
            c=self.pid
        )

    @property
    def result(self):
        """Empty attribute to hold the result of requests to get OCR data."""
        words = Annotation.objects.filter(
            owner=USER.objects.get(username='ocr'),
            canvas=self.id).order_by('order')
        clean_words = []
        for word in words:
            clean_word = BeautifulSoup(word.content, 'html.parser').text
            clean_words.append(clean_word)
        return ' '.join(clean_words)

    def save(self, *args, **kwargs): # pylint: disable = arguments-differ
        """Override save function to add OCR on save."""
        if self._state.adding or not self.annotation_set.all().exists():
            self.__add_ocr()
        super(Canvas, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.pid)

    def __add_ocr(self):
        """Private function for parsing and adding OCR."""
        word_order = 1
        ocr = services.get_ocr(self)
        if ocr is not None:
            for word in ocr:
                if (
                        word == '' or
                        'content' not in word or
                        not word['content'] or
                        word['content'].isspace()
                ):
                    continue
                anno = Annotation()
                anno.canvas = self
                anno.x = word['x']
                anno.y = word['y']
                anno.w = word['w']
                anno.h = word['h']
                anno.resource_type = anno.OCR
                anno.content = word['content']
                anno.order = word_order
                anno.save()
                word_order += 1

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        ordering = ['position']

@receiver(signals.pre_save, sender=Canvas)
def set_dimensions(sender, instance, **kwargs):
    """Pre-save function to get the width and height of the image."""
    if instance.image_info:
        instance.width = instance.image_info['width']
        instance.height = instance.image_info['height']

class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        # Translators: admin:skip
    verbose_name = 'canvas'
    # Translators: admin:skip
    verbose_name_plural = 'canvases'
    app_label = 'canvas'
