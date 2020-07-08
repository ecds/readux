"""Django models for IIIF manifests"""
from uuid import uuid4, UUID
from json import JSONEncoder
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.aggregates import StringAgg
from modelcluster.models import ClusterableModel
import config.settings.local as settings
from ..kollections.models import Collection

JSONEncoder_olddefault = JSONEncoder.default # pylint: disable = invalid-name

def JSONEncoder_newdefault(self, o): # pylint: disable = invalid-name
    """This JSONEncoder makes Wagtail autocomplete run - do not delete."""
    if isinstance(o, UUID):
        return str(o)
    return JSONEncoder_olddefault(self, o)
JSONEncoder.default = JSONEncoder_newdefault

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

class Manifest(ClusterableModel):
    """Model class for IIIF Manifest"""

    DIRECTIONS = (
        ('left-to-right', 'Left to Right'),
        ('right-to-left', 'Right to Left')
    )
    id = models.UUIDField(primary_key=True, default=uuid4, editable=True)
    pid = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    summary = models.TextField()
    author = models.TextField(null=True)
    published_city = models.TextField(null=True)
    published_date = models.CharField(max_length=25)
    publisher = models.CharField(max_length=255)
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
    pdf = models.URLField()
    metadata = JSONField(default=dict, blank=True)
    viewingDirection = models.CharField(max_length=13, choices=DIRECTIONS, default="left-to-right")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    autocomplete_search_field = 'label'
    search_vector = SearchVectorField(null=True, editable=False)
    objects = ManifestManager()
    start_canvas = models.ForeignKey(
        'canvases.Canvas',
        on_delete=models.DO_NOTHING,
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

    # TODO: Maybe this should return the canvas object so we can replace
    # the logic in the serializer that basically makes this same query
    # to get the thumbnail.
    # @property
    # def start_canvas(self):
    #     """Identifier for first canvas for manifest.

    #     :rtype: str
    #     """
    #     first = self.canvas_set.all().exclude(is_starting_page=False).first()
    #     return first.identifier if first else self.canvas_set.all().first().identifier

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
        if self.start_canvas is None and self.canvas_set.exists():
            self.start_canvas = self.canvas_set.first()

        super().save(*args, **kwargs)

        if 'update_fields' not in kwargs or 'search_vector' not in kwargs['update_fields']:
            instance = self._meta.default_manager.with_documents().get(pk=self.pk)
            instance.search_vector = instance.document
            instance.save(update_fields=['search_vector'])

# TODO: is this needed?
class Note(models.Model):
    """Note for manifest"""
    label = models.CharField(max_length=255)
    language = models.CharField(max_length=10, default='en')
    manifest = models.ForeignKey(Manifest, null=True, on_delete=models.CASCADE)
