from django.db import models
import config.settings.local as settings
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from ..manifests.models import Manifest
from . import services
import uuid

class Canvas(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    pid = models.CharField(max_length=255)
    summary = models.TextField()
    manifest = models.ForeignKey(Manifest, on_delete=models.CASCADE)
    position = models.IntegerField()
    height = models.IntegerField(default=0)
    width = models.IntegerField(default=0)

    @property
    def identifier(self):
      return "%s/iiif/%s/canvas/%s" % (settings.HOSTNAME, self.manifest.pid, self.pid)

    @property
    def service_id(self):
      return "%s/%s" % (settings.IIIF_IMAGE_SERVER_BASE, self.pid)

    @property
    def image_info(self):
        return services.get_canvas_info(self)

    @property
    def thumbnail(self):
        return "%s/%s/full/200,250/0/default.jpg" % (settings.IIIF_IMAGE_SERVER_BASE, self.pid)
    
    class Meta:
        ordering = ['position']

@receiver(signals.pre_save, sender=Canvas)
def set_dimensions(sender, instance, **kwargs):
    if instance.image_info:
      instance.width = instance.image_info['width']
      instance.height = instance.image_info['height']

class Meta:
    # Translators: admin:skip
    verbose_name = _('MANIFEST.NAME.LABEL')
    # Translators: admin:skip
    verbose_name_plural = _('MANIFEST.NAME.PLURAL')
