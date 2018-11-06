from django.db import models
import config.settings.local as settings
from ..manifests.models import Manifest
from . import services
import uuid

"""
V2
{
  // Metadata about this canvas
  "@context": "http://iiif.io/api/presentation/2/context.json",
  "@id": "http://example.org/iiif/book1/canvas/p1",
  "@type": "sc:Canvas",
  "label": "p. 1",
  "height": 1000,
  "width": 750,
  "thumbnail" : {
    "@id" : "http://example.org/iiif/book1/canvas/p1/thumb.jpg",
    "@type": "dctypes:Image",
    "height": 200,
    "width": 150
  },
  "images": [
    {
      "@type": "oa:Annotation"
      // Link from Image to canvas should be included here, as below
    }
  ],
  "otherContent": [
    {
      // Reference to list of other Content resources, _not included directly_
      "@id": "http://example.org/iiif/book1/list/p1",
      "@type": "sc:AnnotationList"
    }
  ]

}

V3
{
  // Metadata about this canvas
  "id": "https://example.org/iiif/book1/canvas/p1",
  "type": "Canvas",
  "label": { "@none": [ "p. 1" ] },
  "height": 1000,
  "width": 750,

  "items": [
    {
      "id": "https://example.org/iiif/book1/page/p1/1",
      "type": "AnnotationPage",
      "items": [
        // Content Annotations on the Canvas are included here
      ]
    }
  ]
}
"""

class Canvas(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    pid = models.CharField(max_length=255)
    summary = models.TextField()
    manifest = models.ForeignKey(Manifest, on_delete=models.CASCADE)
    position = models.IntegerField()

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
    def width(self):
        if self.image_info:
            return self.image_info['width']
    
    @property
    def height(self):
        if self.image_info:
            return self.image_info['height']

    @property
    def thumbnail(self):
        return "%s/%s/full/200,250/0/default.jpg" % (settings.IIIF_IMAGE_SERVER_BASE, self.pid)
    
    class Meta:
        ordering = ['position']
