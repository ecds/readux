"""Django models representing IIIF canvases and IIIF image server info."""
import uuid
from bs4 import BeautifulSoup
import tempfile
from urllib.parse import quote
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

# TODO: This has moved to Manifest. Remove one everyone has migrated.
# class IServer(models.Model):
#     """Django model for IIIF image server info. Each canvas has one IServer"""
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     IIIF_IMAGE_SERVER_BASE = models.CharField(
#         max_length=255,
#         default=settings.IIIF_IMAGE_SERVER_BASE
#     )

#     def __str__(self):
#         return "%s" % (self.IIIF_IMAGE_SERVER_BASE)

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
    ocr_offset = models.IntegerField(default=0)
    resource = models.TextField(blank=True, null=True)
    # TODO: This has moved to Manifest. Remove one everyone has migrated.
    # IIIF_IMAGE_SERVER_BASE = models.ForeignKey(IServer, on_delete=models.CASCADE, null=True)
    is_starting_page = models.BooleanField(default=False)
    preferred_ocr = (
        ('word', 'word'),
        ('line', 'line'),
        ('both', 'both')
    )
    # TODO: move this to the mainfest level.
    default_ocr = models.CharField(max_length=30, choices=preferred_ocr, default="word")
    ocr_file_path = models.FilePathField(path=tempfile.gettempdir(), recursive=True, allow_folders=True, null=True, blank=True)

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
            h=self.manifest.image_server.server_base,
            c=quote(self.pid)
        )

    @property
    def resource_id(self):
        """Concatenated propert to represent IIIF resource id."""
        return '{h}/{r}'.format(
            h=self.manifest.image_server.server_base,
            r=self.resource or self.pid
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
        print(self)
        """Convenience property for the canvas' IIIF info json URL."""
        return services.get_canvas_info(self)

    @property
    def thumbnail(self):
        """Concatenated property to represent IIIF thumbnail link."""
        return self.resource_id + '/full/200,/0/default.jpg'
        # return '{h}/{c}/full/200,/0/default.jpg'.format(
        #     h=self.manifest.image_server.server_base,
        #     c=self.resource
        # )

    @property
    def social_media(self):
        """Concatenated property to represent IIIF image link for use in Open Graph metadata."""
        return '{h}/{c}/full/600,/0/default.jpg'.format(
            h=self.manifest.image_server.server_base,
            c=self.resource
        )

    @property
    def twitter_media1(self):
        """Concatenated property for twitter cards and Open Graph metadata."""
        # TODO: shouldn't this use `self.manifest.image_server.server_base`
        return f'{self.resource_id}/full/600,/0/default.jpg'

    @property
    def twitter_media2(self):
        """Concatenated property for twitter cards and Open Graph metadata."""
        return f'{self.resource_id}/full/600,/0/default.jpg'
        # return '{h}/{c}/full/600,/0/default.jpg'.format(
        #     h=self.manifest.image_server.server_base,
        #     c=self.resource
        # )

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
            return f'{self.resource_id}/full/,250/0/default.jpg'
            # return '{h}/{c}/full/,250/0/default.jpg'.format(
            #     h=self.manifest.image_server.server_base,
            #     c=self.resource
            # )
        # landscape
        return f'{self.resource_id}/pct:25,0,50,100/,250/0/default.jpg'
        # return '{h}/{c}/pct:25,0,50,100/,250/0/default.jpg'.format(
        #     h=self.manifest.image_server.server_base,
        #     c=self.resource
        # )

    @property
    def thumbnail_crop_tallwide(self):
        """Concatenated property for cropped tallwide URI"""
        if self.height > self.width:
            # portrait
            return '{h}/{c}/pct:5,5,90,90/,250/0/default.jpg'.format(
                h=self.manifest.image_server.server_base,
                c=self.resource
            )
        # landscape
        return "%s/%s/pct:5,5,90,90/250,/0/default.jpg" % (self.manifest.image_server.server_base, self.resource)

    @property
    def thumbnail_crop_volume(self):
        """Concatenated property for cropped volume URI"""
        if self.height > self.width:
            # portrait
            return f'{self.resource_id}/pct:15,15,70,70/,600/0/default.jpg'
            # return '{h}/{c}/pct:15,15,70,70/,600/0/default.jpg'.format(
            #     h=self.manifest.image_server.server_base,
            #     c=self.resource
            # )
        # landscape
        return f'{self.resource_id}/pct:25,15,50,85/,600/0/default.jpg'
        # return '{h}/{c}/pct:25,15,50,85/,600/0/default.jpg'.format(
        #     h=self.manifest.image_server.server_base,
        #     c=self.resource
        # )

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
        """
        Override save function to set `resource_id` add OCR,
        and set as manifest's `start_canvas` if manifest does not have one.
        """
        if self.resource is None:
            self.resource = self.pid

        super(Canvas, self).save(*args, **kwargs)

        if self._state.adding or not self.annotation_set.exists():
            self.__add_ocr()


        if self.manifest and self.manifest.start_canvas is None:
            self.manifest.save()


    def __str__(self):
        return str(self.pid)

    def __add_ocr(self):
        """Private function for parsing and adding OCR."""
        word_order = 1
        ocr = services.get_ocr(self)
        if ocr is not None:
            for word in ocr:
                # A quick check to make sure the header row didn't slip through.
                if word['x'] == 'x':
                    continue

                # Set the content to a single space if it's missing.
                if (
                        word == '' or
                        'content' not in word or
                        not word['content'] or
                        word['content'].isspace()
                ):
                    word['content'] = ' '
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
