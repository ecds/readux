"""Django models for IIIF manifests"""
from boto3 import resource
from uuid import uuid4, UUID
from json import JSONEncoder
from django.apps import apps
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from modelcluster.models import ClusterableModel
import config.settings.local as settings
from ..choices import Choices
from ..kollections.models import Collection
from..models import IiifBase
JSONEncoder_olddefault = JSONEncoder.default # pylint: disable = invalid-name

def JSONEncoder_newdefault(self, o): # pylint: disable = invalid-name
    """This JSONEncoder makes Wagtail autocomplete run - do not delete."""
    if isinstance(o, UUID):
        return str(o)
    return JSONEncoder_olddefault(self, o)
JSONEncoder.default = JSONEncoder_newdefault

class ImageServer(models.Model):
    """Django model for IIIF image server info. Each canvas has one ImageServer"""

    STORAGE_SERVICES = (
        ('sftp', 'SFTP'),
        ('s3', 'S3'),
        ('remote', 'Remote'),
    )

    id = models.UUIDField(primary_key=True, default=uuid4)
    server_base = models.CharField(
        max_length=255,
        default=settings.IIIF_IMAGE_SERVER_BASE
    )
    storage_service = models.CharField(max_length=10, choices=STORAGE_SERVICES, default='sftp')
    storage_path = models.CharField(max_length=255)

    def __str__(self):
        return "%s" % (self.server_base)

    @property
    def bucket(self):
        if self.storage_service == 's3':
            s3 = resource('s3')
            return s3.Bucket(self.storage_path)
        return None

class ValueByLanguage(models.Model):
    """ Labels by language. """
    id = models.UUIDField(primary_key=True, default=uuid4)
    language = models.CharField(max_length=10, choices=Choices.LANGUAGES, default=settings.DEFAULT_LANGUAGE)
    content = models.TextField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')

class ManifestManager(models.Manager): # pylint: disable = too-few-public-methods
    """Model manager for searches."""
    def with_documents(self):
        """[summary]

        :param models: [description]
        :type models: [type]
        :return: [description]
        :rtype: django.db.models.QuerySet
        """
        vector = SearchVector(StringAgg('canvas__annotation__content', delimiter=' '))
        return self.get_queryset().annotate(document=vector)

class Manifest(IiifBase):
    """Model class for IIIF Manifest"""

    DIRECTIONS = (
        ('left-to-right', 'Left to Right'),
        ('right-to-left', 'Right to Left')
    )
    summary = models.TextField(null=True, blank=True)
    author = models.TextField(null=True, blank=True, help_text="Enter multiple entities separated by a semicolon (;).")
    published_city = models.TextField(null=True, blank=True, help_text="Enter multiple entities separated by a semicolon (;).")
    published_date = models.CharField(max_length=25, null=True, blank=True)
    publisher = models.TextField(null=True, blank=True, help_text="Enter multiple entities separated by a semicolon (;).")
    attribution = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default="Emory University Libraries",
        help_text="The institution holding the manifest"
    )
    logo = models.ImageField(
        upload_to='logos/',
        null=True, blank=True,
        default="logos/lits-logo-web.png",
        help_text="Upload the Logo of the institution holding the manifest."
    )
    license = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default="https://creativecommons.org/publicdomain/zero/1.0/",
        help_text="Only enter a URI to a license statement."
    )
    collections = models.ManyToManyField(Collection, blank=True, related_name='manifests')
    pdf = models.URLField(null=True, blank=True)
    metadata = JSONField(default=dict, blank=True)
    viewingdirection = models.CharField(max_length=13, choices=DIRECTIONS, default="left-to-right")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    autocomplete_search_field = 'label'
    # TODO: This has to be removed/redone before we upgrade to Django 3
    search_vector = SearchVectorField(null=True, editable=False)
    image_server = models.ForeignKey(ImageServer, on_delete=models.DO_NOTHING, null=True)
    objects = ManifestManager()
    start_canvas = models.ForeignKey(
        'canvases.Canvas',
        on_delete=models.SET_NULL,
        related_name='start_canvas',
        blank=True,
        null=True
    )

    def get_absolute_url(self):
        """Absolute URL for manifest

        :return: Manifest's absolute URL
        :rtype: str
        """
        return '{h}/volume/{p}'.format(h=settings.HOSTNAME, p=self.pid)

    def get_volume_url(self):
        """Convenience method for IIIF qualified URL.

        :return: IIIF manifest URL
        :rtype: str
        """
        return '{h}/volume/{p}/page/all'.format(h=settings.HOSTNAME, p=self.pid)

    class Meta: # pylint: disable = too-few-public-methods, missing-class-docstring
        ordering = ['published_date']
        indexes = [GinIndex(fields=['search_vector'])]

    @property
    def publisher_bib(self):
        """Concatenated property for bib citation.

        :rtype: str
        """
        return '{c} : {p}'.format(c=self.published_city, p=self.publisher)

    @property
    def thumbnail_logo(self):
        """Thumbnail of holding institution's logo

        :return: URL for logo thumbnail.
        :rtype: str
        """
        return '{h}/media/{l}'.format(h=settings.HOSTNAME, l=self.logo)

    @property
    def baseurl(self):
        """Convenience method to provide the base URL for a manifest."""
        return "%s/iiif/v2/%s" % (settings.HOSTNAME, self.pid)

    @property
    def related_links(self):
        """List of links for IIIF v2 'related' field.

        :return: List of links related to Manifest
        :rtype: list
        """
        links = [link.link for link in self.relatedlink_set.all()]
        links.append(self.get_volume_url())
        return links

    # TODO: Is this needed? It doesn't seem to be called anywhere.
    # Could we just use the label as is?
    def autocomplete_label(self):
        """Label of manifest.

        :rtype: str
        """
        return self.label

    def __str__(self):
        return self.label

    # FIXME: This creates a circular dependency - Importing UserAnnotation here.
    # Furthermore, we shouldn't have any of the IIIF apps depend on Readux. Need
    # to figure out a different, but still efficient way of doing this.
    def user_annotation_count(self, user=None):
        if user is None:
            return None
        from apps.readux.models import UserAnnotation
        return UserAnnotation.objects.filter(owner=user).filter(canvas__manifest=self).count()

    #update search_vector every time the entry updates
    def save(self, *args, **kwargs): # pylint: disable = arguments-differ

        if not self._state.adding and 'pid' in self.get_dirty_fields() and self.image_server and self.image_server.storage_service == 's3':
            self.__rename_s3_objects()

        super().save(*args, **kwargs)

        Canvas = apps.get_model('canvases.canvas')
        try:
            if self.start_canvas is None and hasattr(self, 'canvas_set') and self.canvas_set.exists():
                print([c.position] for c in self.canvas_set.all())
                self.start_canvas = self.canvas_set.all().order_by('position').first()
                self.save()
        except Canvas.DoesNotExist:
            self.start_canvas = None

        if 'update_fields' not in kwargs or 'search_vector' not in kwargs['update_fields']:
            instance = self._meta.default_manager.with_documents().get(pk=self.pk)
            instance.search_vector = instance.document
            instance.save(update_fields=['search_vector'])


    def delete(self, *args, **kwargs):
        """
        When a manifest is delted, the related canvas objects are deleted (`on_delete`=models.CASCADE).
        However, the `delete` method is not called on the canvas objects. We need to do that so
        the files can be cleaned up.
        https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.CASCADE
        """
        for canvas in self.canvas_set.all():
            canvas.delete()

        super().delete(*args, **kwargs)

    def __rename_s3_objects(self):
        original_pid = self.get_dirty_fields()['pid']
        keys = [f.key for f in self.image_server.bucket.objects.filter(Prefix=f'{original_pid}/')]
        for key in keys:
            obj = self.image_server.bucket.Object(key.replace(original_pid, self.pid))
            obj.copy({ 'Bucket': self.image_server.storage_path, 'Key': key })
            self.image_server.bucket.Object(key).delete()

# TODO: is this needed?
class Note(models.Model):
    """Note for manifest"""
    label = models.CharField(max_length=255)
    language = models.CharField(max_length=10, default='en')
    manifest = models.ForeignKey(Manifest, null=True, on_delete=models.CASCADE)

class RelatedLink(models.Model):
    """ Links to related resources """
    id = models.UUIDField(primary_key=True, default=uuid4)
    link = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255, default='Dataset')
    label = GenericRelation(ValueByLanguage)
    format = models.CharField(max_length=255, choices=Choices.MIMETYPES, blank=True, null=True)
    profile = models.CharField(max_length=255, blank=True, null=True)
    manifest = models.ForeignKey(Manifest, on_delete=models.CASCADE)
