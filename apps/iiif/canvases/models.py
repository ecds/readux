"""Django models representing IIIF canvases and IIIF image server info."""
from genericpath import exists
import os
from boto3 import resource
from bs4 import BeautifulSoup
from urllib.parse import quote
import config.settings.local as settings
from django.db import models
from django.contrib.auth import get_user_model
from ..models import IiifBase
from ..manifests.models import Manifest, ImageServer
from ..annotations.models import Annotation
from . import services

USER = get_user_model()

class Canvas(IiifBase):
    """Django model for IIIF Canvas objects."""
    summary = models.TextField(blank=True, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.CASCADE)
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    position = models.IntegerField()
    height = models.IntegerField(default=0)
    width = models.IntegerField(default=0)
    ocr_offset = models.IntegerField(default=0)
    resource = models.TextField(blank=True, null=True)
    is_starting_page = models.BooleanField(default=False)
    preferred_ocr = (
        ('word', 'word'),
        ('line', 'line'),
        ('both', 'both')
    )
    # TODO: move this to the mainfest level.
    default_ocr = models.CharField(max_length=30, choices=preferred_ocr, default="word")
    ocr_file_path = models.CharField(max_length=500, null=True, blank=True)

    @property
    def file_name(self):
        return self.pid.replace('_', '/')

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
        self.__check_image_server()
        if self.image_server is None:

            return None

        return f'{self.image_server.server_base}/{quote(self.pid)}'

    @property
    def resource_id(self):
        """Concatenated property to represent IIIF resource id."""
        self.__check_image_server()
        if self.image_server is None:
            return None

        return f'{self.image_server.server_base}/{self.resource}'

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
        return self.resource_id + '/full/200,/0/default.jpg'

    @property
    def social_media(self):
        """Concatenated property to represent IIIF image link for use in Open Graph metadata."""
        self.__check_image_server()

        if self.image_server is None:
            return None

        return '{h}/{c}/full/600,/0/default.jpg'.format(
            h=self.image_server.server_base,
            c=self.resource
        )

    @property
    def twitter_media1(self):
        """Concatenated property for twitter cards and Open Graph metadata."""
        # TODO: shouldn't this use `self.image_server.server_base`
        return f'{self.resource_id}/full/600,/0/default.jpg'

    @property
    def twitter_media2(self):
        """Concatenated property for twitter cards and Open Graph metadata."""
        return f'{self.resource_id}/full/600,/0/default.jpg'

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
        # landscape
        return f'{self.resource_id}/pct:25,0,50,100/,250/0/default.jpg'

    @property
    def thumbnail_crop_tallwide(self):
        """Concatenated property for cropped tallwide URI"""
        if self.height > self.width:
            # portrait
            return f'{self.resource_id}/pct:5,5,90,90/,250/0/default.jpg'
        # landscape
        return f'{self.resource_id}/pct:5,5,90,90/250,/0/default.jpg'

    @property
    def thumbnail_crop_volume(self):
        """Concatenated property for cropped volume URI"""
        if self.height > self.width:
            # portrait
            return f'{self.resource_id}/pct:15,15,70,70/,600/0/default.jpg'
        # landscape
        return f'{self.resource_id}/pct:25,15,50,85/,600/0/default.jpg'

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

    def save(self, *args, **kwargs): # pylint: disable = signature-differs
        """
        Override save function to set `resource_id` add OCR,
        set as manifest's `start_canvas` if manifest does not have one,
        and set
        """
        self.__check_image_server()

        if self.manifest and self.position is None:
            self.position = self.manifest.canvas_set.count() + 1

        if self.image_info:
            # TODO: Consider changing the default value for height and width
            # so we don't have to check for 0 in addition to None.
            if self.width == 0 or self.height == 0:
                self.width = None
                self.height = None
            if self.width is None and self.height is None:
                self.width = self.image_info['width']
                self.height = self.image_info['height']

        super().save(*args, **kwargs)

        if self.resource is None:
            self.resource = self.pid
            self.save()

        if self.manifest and self.manifest.start_canvas is None:
            self.manifest.save()

    def delete(self, *args, **kwargs):
        """
        Override the delete function to clean up files.
        """
        if self.image_server.storage_service == 's3':
            s3 = resource('s3')
            s3.Object(self.image_server.storage_path, self.file_name).delete()

            if self.ocr_file_path:
                ocr_file = self.ocr_file_path.split("/")[-1]
                key = f'{self.manifest.pid}/_*ocr*_/{ocr_file}'
                s3.Object(self.image_server.storage_path, key).delete()
        else:
            try:
                os.remove(os.path.join(self.image_server.storage_path, self.file_name))
            except (FileNotFoundError, TypeError):
                pass
            try:
                os.remove(self.ocr_file_path)
            except (FileNotFoundError, TypeError):
                pass


        super().delete(*args, **kwargs)

    # TODO: The way we construct PIDs for Canvas objects might need some
    # rethinking.
    def clean_pid(self):
        """ Override the `__clean_pid` method that replaces underscores (_).
        Canvas PIDs are combonation of the Manifest PID and the Canvase's
        file name, seperated by an underscore. This is how Cantaloupe finds
        the image file. """
        pass

    def __str__(self):
        return str(self.pid)

    def __check_image_server(self):
        try:
            if self.image_server is None and self.manifest.image_server is not None:
                self.image_server = self.manifest.image_server
        except Manifest.DoesNotExist:
            return None

    class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
        ordering = ['position']

class Meta: # pylint: disable=too-few-public-methods, missing-class-docstring
    verbose_name = 'canvas'
    # Translators: admin:skip
    verbose_name_plural = 'canvases'
    app_label = 'canvas'
