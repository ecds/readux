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

def get_default_iiif_setting():
  return "%s" % (settings.IIIF_IMAGE_SERVER_BASE)

class IServer(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    IIIF_IMAGE_SERVER_BASE = models.CharField(max_length=255, default=get_default_iiif_setting)

    def __str__(self):
        return "%s" % (self.IIIF_IMAGE_SERVER_BASE)

class Canvas(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    pid = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.CASCADE)
    position = models.IntegerField()
    height = models.IntegerField(default=0)
    width = models.IntegerField(default=0)
    IIIF_IMAGE_SERVER_BASE = models.ForeignKey(IServer, on_delete=models.CASCADE, null=True)

    @property
    def identifier(self):
      return "%s/iiif/%s/canvas/%s" % (settings.HOSTNAME, self.manifest.pid, self.pid)

    @property
    def service_id(self):
      return "%s/%s" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def image_info(self):
        return services.get_canvas_info(self)

    @property
    def thumbnail(self):
        return "%s/%s/full/200,250/0/default.jpg" % (self.IIIF_IMAGE_SERVER_BASE, self.pid)
    
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
    ocr = services.add_positional_ocr(instance)
    # What comes back from fedora is 8-bit bytes
    # https://stackoverflow.com/a/9562196
    word_order = 1
    if ocr is not None:
        for word in ocr.decode('UTF-8-sig').strip().split('\r\n'):
            if word == '':
                continue
            a = Annotation()
            a.canvas = instance
            print('&&&')
            print(word)
            a.x = int(word.split('\t')[0])
            a.y = int(word.split('\t')[1])
            a.w = int(word.split('\t')[2])
            a.h = int(word.split('\t')[3])
            a.resource_type = a.OCR
            a.content = word.split('\t')[4]
            a.order = word_order
            a.save()
            word_order += 1

class Meta:
    # Translators: admin:skip
    verbose_name = 'canvas'
    # Translators: admin:skip
    verbose_name_plural = 'canvases'
    app_label = 'canvas'
