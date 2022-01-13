"""Django model for Collection app"""
import os.path
import uuid
from io import BytesIO
from PIL import Image
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.files.base import ContentFile
import config.settings.local as settings
from ..models import IiifBase

class Collection(IiifBase):
    """Model for IIIF Collection."""
    summary = models.TextField(
        help_text="Description of the collection."
    )
    attribution = models.CharField(
        max_length=255,
        null=True,
        help_text="Repository holding the collection. List multiple if the manifests are from multiple collections." # pylint: disable = line-too-long
    )
    metadata = JSONField(null=True)
    upload = models.FileField(upload_to='uploads/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    original = models.ImageField(
        upload_to='originals/', #I'm not deleting this field yet, since that would mess more with existing data - and we may want to use this field for something else later.
        null=True,
        blank=True,
        help_text="No longer used!" # pylint: disable = line-too-long
    )
    header = models.ImageField(
        upload_to='headers/',
        null=True,
        help_text="Upload the image for the collection header here. Ideal ratio 1200 x 300 px."
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/',
        null=True,
        help_text="Upload the image for the collection thumbnail here. Ideal ratio 400 x 500 px."
    )
    collection_image_title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The title of the header image."
    )
    collection_image_creator = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The artist or author of the header image source."
    )
    collection_image_summary = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Any additional information to display about the header image source."
    )
    autocomplete_search_field = 'label'

    # TODO: Why can we not just use the label attribute directly? Or `self.__str__`?
    def autocomplete_label(self):
        """Label for autocomplete UI element

        :return: Label of collection
        :rtype: str
        """
        return self.label

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        """Concatenated property for collection's URI"""
        return "%s/collection/%s" % (settings.HOSTNAME, self.pid)

    def save(self, *args, **kwargs): # pylint: disable = arguments-differ
        """Override save function to create the the thumbnail file for the collection"""
        if not self.__make_thumbnail():
            # set to a default thumbnail
            raise Exception('Could not create thumbnail - is the file type valid?')
        if not self.__make_header():
            # set to a default header
            raise Exception('Could not create header - is the file type valid?')

        super(Collection, self).save(*args, **kwargs)

    # TODO: Maybe we should move this to a service and break it up a bit.
    def __make_thumbnail(self):
        """Private method to generate a thumbnail for the collection.

        :return: True if file is created successfully.
        :rtype: bool
        """
        # If height is higher we resize vertically, if not we resize horizontally
        size = (400, 500)
        image = Image.open(self.thumbnail)
        # Get current and desired ratio for the images
        img_ratio = image.size[0] / float(image.size[1])
        ratio = size[0] / float(size[1])
        #The image is scaled/cropped vertically or horizontally depending on the ratio
        if ratio > img_ratio:
            image = image.resize(
                (int(size[0]), int(size[0] * image.size[1] / image.size[0])),
                Image.ANTIALIAS)
            # Crop in the top, middle or bottom
            box = (0, (image.size[1] - size[1]) / 2, image.size[0], (image.size[1] + size[1]) / 2)
            image = image.crop(box)
        elif ratio < img_ratio:
            imageratio = (int(size[1] * image.size[0] / image.size[1]), int(size[1]))
            image = image.resize(imageratio, Image.ANTIALIAS)
            box = ((image.size[0] - size[0]) / 2, 0, (image.size[0] + size[0]) / 2, image.size[1])
            image = image.crop(box)
        else:
            image = image.resize((size[0], size[1]), Image.ANTIALIAS)
        # If the scale is the same, we do not need to crop
        thumb_name, thumb_extension = os.path.splitext(self.thumbnail.name)
        thumb_extension = thumb_extension.lower()

        thumb_filename = thumb_name + '_thumb' + thumb_extension

        if thumb_extension in ['.jpg', '.jpeg']:
            file_type = 'JPEG'
        elif thumb_extension == '.gif':
            file_type = 'GIF'
        elif thumb_extension == '.png':
            file_type = 'PNG'
        else:
            return False    # Unrecognized file type

        # Save thumbnail to in-memory file as StringIO
        temp_thumb = BytesIO()
        image.save(temp_thumb, file_type)
        temp_thumb.seek(0)

        # set save=False, otherwise it will run in an infinite loop
        self.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
        temp_thumb.close()
        return True

    def __make_header(self):
        """Private method to generate a thumbnail for the collection.

        :return: True if file is created successfully.
        :rtype: bool
        """
        # If height is higher we resize vertically, if not we resize horizontally
        sizebanner = (1200, 300)
        forcrop = Image.open(self.header)
        # Get current and desired ratio for the images
        img_ratio_banner = forcrop.size[0] / float(forcrop.size[1])
        ratio_banner = sizebanner[0] / float(sizebanner[1])
        #The image is scaled/cropped vertically or horizontally depending on the ratio
        if ratio_banner > img_ratio_banner: #then it needs to be shorter
            forcrop = forcrop.resize(
                (int(sizebanner[0]), int(sizebanner[0] * forcrop.size[1] / forcrop.size[0])),
                Image.ANTIALIAS)
            (width, height) = forcrop.size
            # pylint: disable = invalid-name
            x = (0)
            y = (height - sizebanner[1]) / 2
            w = width
            h = (height + sizebanner[1]) / 2
            # pylint: enable = invalid-name

            box = (x, y, w, h)
            cropped_image = forcrop.crop(box)
            # Crop in the top, middle or bottom
        elif ratio_banner < img_ratio_banner: #then it needs to be narrower
            imagebannerratio = (int(sizebanner[1] * forcrop.size[0] / forcrop.size[1]), int(sizebanner[1]))
            forcrop = forcrop.resize(imagebannerratio, Image.ANTIALIAS)
            (width, height) = forcrop.size
            # pylint: disable = invalid-name
            x = (width - sizebanner[0]) / 2 #crop from middle
            y = (0)
            w = (width + sizebanner[0]) / 2
            h = height
            # pylint: enable = invalid-name

            box = (x, y, w, h)
            cropped_image = forcrop.crop(box)
        else:
            cropped_image = forcrop.resize((sizebanner[0], sizebanner[1]), Image.ANTIALIAS)
        # If the scale is the same, we do not need to crop
        thename, theextension = os.path.splitext(self.header.name)
        theextension = theextension.lower()

        thefilename = thename + '_header' + theextension

        if theextension in ['.jpg', '.jpeg']:
            file_type = 'JPEG'
        elif theextension == '.gif':
            file_type = 'GIF'
        elif theextension == '.png':
            file_type = 'PNG'
        else:
            return False    # Unrecognized file type

        # Save header to in-memory file as StringIO
        temp_header = BytesIO()
        cropped_image.save(temp_header, file_type)
        temp_header.seek(0)

        # set save=False, otherwise it will run in an infinite loop
        self.header.save(thefilename, ContentFile(temp_header.read()), save=False)
        temp_header.close()

        return True
