"""Django model for Collection app"""
import os.path
import uuid
from io import BytesIO
from PIL import Image
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.files.base import ContentFile
import config.settings.local as settings

class Collection(models.Model):
    """Model for IIIF Collection."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, help_text="Title of the collection.")
    summary = models.TextField(
        help_text="Description of the collection."
    )
    pid = models.CharField(
        max_length=255,
        help_text="Unique ID. Do not use -'s or spaces in the pid."
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
        upload_to='originals/',
        null=True,
        help_text="Upload the Original Image and the Thumbnail and Banner will be created automatically!" # pylint: disable = line-too-long
    )
    header = models.ImageField(
        upload_to='headers/',
        null=True,
        blank=True,
        help_text="You do not need to upload this file."
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/',
        null=True,
        blank=True,
        help_text="You do not need to upload this file."
    )
    collection_image_title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The title of the header/thumbnail image."
    )
    collection_image_creator = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The artist or author of the header/thumbnail image source."
    )
    collection_image_summary = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Any additional information to display about the header/thumbnail image source."
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

        super(Collection, self).save(*args, **kwargs)

    # TODO: Maybe we should move this to a service and break it up a bit.
    def __make_thumbnail(self):
        """Private method to generate a thumbnail for the collection.

        :return: True if file is created successfully.
        :rtype: bool
        """
        # If height is higher we resize vertically, if not we resize horizontally
        size = (400, 500)
        image = Image.open(self.original)
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
        thumb_name, thumb_extension = os.path.splitext(self.original.name)
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

        forcrop = Image.open(self.original)
        (width, height) = forcrop.size
        # pylint: disable = invalid-name
        x = (0)
        y = height/3
        w = width
        h = 2 * height/3
        # pylint: enable = invalid-name

        box = (x, y, w, h)
        cropped_image = forcrop.crop(box)

        thename, theextension = os.path.splitext(self.original.name)
        theextension = theextension.lower()

        thefilename = thename + '_header' + theextension

        header_io = BytesIO()
        cropped_image.save(header_io, format=file_type)
        header_io.seek(0)

        self.header.save(thefilename, ContentFile(header_io.read()), save=False)
        header_io.close()
        temp_thumb.close()

        return True
