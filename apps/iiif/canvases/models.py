from django.db import models
import config.settings.local as settings
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from ..manifests.models import Manifest
from ..annotations.models import Annotation
from django.apps import apps
from . import services
import uuid
from bs4 import BeautifulSoup

# TODO: add a test fixture that calls this.
def get_default_iiif_setting():
  return "%s" % (settings.IIIF_IMAGE_SERVER_BASE)

# TODO: move this to the manifest model
class IServer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    IIIF_IMAGE_SERVER_BASE = models.CharField(max_length=255, default=get_default_iiif_setting)

    def __str__(self):
        return "%s" % (self.IIIF_IMAGE_SERVER_BASE)

class Canvas(models.Model):
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
      return "%s/iiif/%s/canvas/%s" % (settings.HOSTNAME, self.manifest.pid, self.pid)

    @property
    def service_id(self):
      return "%s/%s" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def anno_id(self):
      return "%s/iiif/%s/annotation/%s" % (settings.HOSTNAME, self.manifest.pid, self.pid)

    @property
    def image_info(self):
        return services.get_canvas_info(self)

    @property
    def thumbnail(self):
        return "%s/%s/full/200,/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def social_media(self):
        return "%s/%s/full/600,/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    # @property
    # def get_IIIF_IMAGE_SERVER_BASE(self):
    #     return self.IIIF_IMAGE_SERVER_BASE

    @property
    def twitter_media1(self):
        # TODO shouldn't this use `self.IIIF_IMAGE_SERVER_BASE`
        return "http://images.readux.ecds.emory.edu/cantaloupe/iiif/2/%s/full/600,/0/default.jpg" % (self.pid)

    @property
    def twitter_media2(self):
        # TODO shouldn't this use `self.IIIF_IMAGE_SERVER_BASE`
        return "%s/%s/full/600,/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def uri(self):
        return "%s/iiif/%s/" % (settings.HOSTNAME, self.manifest.pid)

    @property
    def thumbnail_crop_landscape(self):
        if self.height > self.width:
            # portrait
            return "%s/%s/full/,250/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)
        else:
            # landscape
            return "%s/%s/pct:25,0,50,100/,250/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def thumbnail_crop_tallwide(self):
        if self.height > self.width:
            # portrait
            return "%s/%s/pct:5,5,90,90/,250/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)
        else:
            # landscape
            return "%s/%s/pct:5,5,90,90/250,/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def thumbnail_crop_volume(self):
        if self.height > self.width:
            # portrait
            return "%s/%s/pct:15,15,70,70/,600/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)
        else:
            # landscape
            # TODO add a landscape image to tests
            return "%s/%s/pct:25,15,50,85/,600/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def result(self):
    #     "Empty attribute to hold the result of requests to get OCR data."
    #     return None
        words = Annotation.objects.filter(canvas=self.id).order_by('order')
        # TODO: The above query really should have a filter for resource_type=OCR but it currently returns an empty set with this parameter set.
        clean_words = []
        for word in words:
            clean_word = BeautifulSoup(word.content, 'html.parser').text
            clean_words.append(clean_word)
        return ' '.join(clean_words)
    
    def save(self, *args, **kwargs):
        if self._state.adding or not self.annotation_set.all().exists():
            self.__add_ocr()
        super(Canvas, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.pid)
    
    def __add_ocr(self):
        word_order = 1
        ocr = services.get_ocr(self)
        if ocr is not None:
            for word in ocr:
                if word == '' or 'content' not in word or not word['content'] or word['content'].isspace():
                    continue
                a = Annotation()
                a.canvas = self
                a.x = word['x']
                a.y = word['y']
                a.w = word['w']
                a.h = word['h']
                a.resource_type = a.OCR
                a.content = word['content']
                a.order = word_order
                a.save()
                word_order += 1

    class Meta:
        ordering = ['position']

@receiver(signals.pre_save, sender=Canvas)
def set_dimensions(sender, instance, **kwargs):
    if instance.image_info:
      instance.width = instance.image_info['width']
      instance.height = instance.image_info['height']

class Meta:
        # Translators: admin:skip
    verbose_name = 'canvas'
    # Translators: admin:skip
    verbose_name_plural = 'canvases'
    app_label = 'canvas'