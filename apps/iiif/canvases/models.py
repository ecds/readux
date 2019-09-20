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

# TODO add a test fixture that calls this.
def get_default_iiif_setting():
  return "%s" % (settings.IIIF_IMAGE_SERVER_BASE)

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
    IIIF_IMAGE_SERVER_BASE = models.ForeignKey(IServer, on_delete=models.CASCADE, null=True)
    is_starting_page = models.BooleanField(default=False)

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

    # @property
    # def result(self):
    #     "Empty attribute to hold the result of requests to get OCR data."
    #     return None

    def __str__(self):
        return str(self.pid)

    class Meta:
        ordering = ['position']

@receiver(signals.pre_save, sender=Canvas)
def set_dimensions(sender, instance, **kwargs):
    if instance.image_info:
      instance.width = instance.image_info['width']
      instance.height = instance.image_info['height']

@receiver(signals.post_save, sender=Canvas)
def add_ocr(sender, instance, **kwargs):
    result = services.fetch_alto_ocr(instance)
    ocr = services.add_alto_ocr(instance, result)
    word_order = 1
    if ocr is not None:
        for word in ocr:
            if word == '':
                continue
            a = Annotation()
            a.canvas = instance
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
    # Translators: admin:skip
    verbose_name = 'canvas'
    # Translators: admin:skip
    verbose_name_plural = 'canvases'
    app_label = 'canvas'
