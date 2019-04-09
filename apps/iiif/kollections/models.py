import os.path
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify
import uuid
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

class Collection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, help_text="Title of the collection.")
    summary = models.TextField(help_text="Description of the collection.")
    pid = models.CharField(max_length=255, help_text="Unique ID. Do not use -'s or spaces in the pid.")
    attribution = models.CharField(max_length=255, null=True, help_text="Repository holding the collection. List multiple if the manifests are from multiple collections.")
    metadata = JSONField(null=True)
    upload = models.FileField(upload_to='uploads/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    original = models.ImageField(upload_to='originals/', null=True, help_text="Upload the Original Image and the Thumbnail and Banner will be created automatically!")
    header = models.ImageField(upload_to='headers/', null=True, blank=True, help_text="You do not need to upload this file.")
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True, help_text="You do not need to upload this file.")
    collection_image_title = models.CharField(max_length=255, null=True, blank=True, help_text="The title of the header/thumbnail image.")
    collection_image_creator = models.CharField(max_length=255, null=True, blank=True, help_text="The artist or author of the header/thumbnail image source.")
    collection_image_summary = models.CharField(max_length=255, null=True, blank=True, help_text="Any additional information to display about the header/thumbnail image source.")
    
    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):

        if not self.make_thumbnail():
            # set to a default thumbnail
            raise Exception('Could not create thumbnail - is the file type valid?')

        super(Collection, self).save(*args, **kwargs)

    def make_thumbnail(self):

        THUMB_SIZE = (200, 250)
        image = Image.open(self.original)
        image.thumbnail(THUMB_SIZE, Image.ANTIALIAS)

        thumb_name, thumb_extension = os.path.splitext(self.original.name)
        thumb_extension = thumb_extension.lower()

        thumb_filename = thumb_name + '_thumb' + thumb_extension

        if thumb_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif thumb_extension == '.gif':
            FTYPE = 'GIF'
        elif thumb_extension == '.png':
            FTYPE = 'PNG'
        else:
            return False    # Unrecognized file type

        # Save thumbnail to in-memory file as StringIO
        temp_thumb = BytesIO()
        image.save(temp_thumb, FTYPE)
        temp_thumb.seek(0)

        # set save=False, otherwise it will run in an infinite loop
        self.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)

        forcrop = Image.open(self.original)
        ( width, height ) = forcrop.size
        x = (0)
        y = height/3
        w = width
        h = 2 * height/3

        box = (x, y, w, h)
        cropped_image = forcrop.crop(box)

        thename, theextension = os.path.splitext(self.original.name)
        theextension = theextension.lower()

        thefilename = thename + '_header' + theextension

        if thumb_extension in ['.jpg', '.jpeg']:
            FtTYPE = 'JPEG'
        elif thumb_extension == '.gif':
            FtTYPE = 'GIF'
        elif thumb_extension == '.png':
            FtTYPE = 'PNG'
        else:
            return False    # Unrecognized file type

        header_io = BytesIO()
        cropped_image.save(header_io, format=FtTYPE)
        header_io.seek(0)
        
        self.header.save(thefilename, ContentFile(header_io.read()), save=False)
        header_io.close()
        temp_thumb.close()
                
        return True

#     def make_header(self):
#         x = (0)
#         y = (0)
#         w = (1000)
#         h = (200)
# 
#         images = Image.open(self.original)
#         images = images.crop((x, y, w+x, h+y))
# 
#         header_io = BytesIO()
#         if thumb_extension in ['.jpg', '.jpeg']:
#             FtTYPE = 'JPEG'
#         elif thumb_extension == '.gif':
#             FtTYPE = 'GIF'
#         elif thumb_extension == '.png':
#             FtTYPE = 'PNG'
#         else:
#             return False    # Unrecognized file type
# 
#         thename, theextension = os.path.splitext(self.original.name)
#         theextension = theextension.lower()
# 
#         thefilename = thename + '_header' + theextension
# 
#         images.save(header_io, format=FtTYPE)
#         header_file = InMemoryUploadedFile(header_io, None, thefilename, FtTYPE, header_io.len, None)
#         self.header.save(thefilename, ContentFile(header_io.read()), save=False)
#         header_io.close()
#                 
#         return True