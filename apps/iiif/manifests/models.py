from django.db import models
import config.settings.local as settings
from ..kollections.models import Collection
from ..annotations.models import Annotation
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
import urllib.request
from modelcluster.models import ClusterableModel
from wagtailautocomplete.edit_handlers import AutocompletePanel
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex
from json import JSONEncoder
from django.contrib.postgres.aggregates import StringAgg
import uuid
from uuid import UUID
#trying to work with autocomplete

User = get_user_model()

JSONEncoder_olddefault = JSONEncoder.default
def JSONEncoder_newdefault(self, o):
    if isinstance(o, UUID): return str(o)
    return JSONEncoder_olddefault(self, o)
JSONEncoder.default = JSONEncoder_newdefault

class ManifestManager(models.Manager):
    def with_documents(self):
        vector = SearchVector(StringAgg('canvas__annotation__content', delimiter=' '))
        return self.get_queryset().annotate(document=vector)
    
class Manifest(ClusterableModel):
    DIRECTIONS = (
        ('left-to-right', 'Left to Right'),
        ('right-to-left', 'Right to Left')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    pid = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    summary = models.TextField()
    author = models.TextField(null=True)
    published_city = models.TextField(null=True)
    published_date = models.CharField(max_length=25)
    publisher = models.CharField(max_length=255)
    attribution = models.CharField(max_length=255, null=True, blank=True, default="Emory University Libraries", help_text="The institution holding the manifest")
    logo = models.ImageField(upload_to='logos/', null=True, blank=True, default="logos/lits-logo-web.png", help_text="Upload the Logo of the institution holding the manifest.")
    license = models.CharField(max_length=255, null=True, blank=True, default="https://creativecommons.org/publicdomain/zero/1.0/", help_text="Only enter a URI to a license statement.")
    #collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name = 'manifest')
    collections = models.ManyToManyField(Collection, null=True, blank=True, related_name = 'manifests')
    pdf = models.URLField()
    metadata = JSONField(default=dict, blank=True)
    viewingDirection = models.CharField(max_length=13, choices=DIRECTIONS, default="left-to-right")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    #starting_page = models.ForeignKey('canvases.Canvas', related_name="first", on_delete=models.SET_NULL, null=True, blank=True, help_text="Choose the page that will show on loading.")
    autocomplete_search_field = 'label'
    search_vector = SearchVectorField(null=True, editable=False)
    objects = ManifestManager()

    def get_absolute_url(self):
        return "%s/volume/%s" % (settings.HOSTNAME, self.pid)

    def get_volume_url(self):
        return "%s/volume/%s/page/all" % (settings.HOSTNAME, self.pid)
    
    class Meta:
        ordering = ['published_date']
        indexes = [GinIndex(fields=['search_vector'])]

    # TODO is this needed?
    # @property
    # def note_list(self):
    #   self.note_set.values('label')[0]['label']

    @property
    def publisher_bib(self):
      return "%s : %s" % (self.published_city, self.publisher)

    @property
    def thumbnail_logo(self):
        return "%s/%s/%s" % (settings.HOSTNAME, "media", self.logo)

    @property
    def baseurl(self):
        return "%s/iiif/v2/%s" % (settings.HOSTNAME, self.pid)

    @property
    def start_canvas(self):
        first = self.canvas_set.all().exclude(is_starting_page=False).first()
        return first.identifier if first else self.canvas_set.all().first().identifier
    
    def autocomplete_label(self):
        return self.label

    def __str__(self):
        return self.label

    #update search_vector every time the entry updates
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if 'update_fields' not in kwargs or 'search_vector' not in kwargs['update_fields']:
            instance = self._meta.default_manager.with_documents().get(pk=self.pk)
            instance.search_vector = instance.document
            instance.save(update_fields=['search_vector'])
        
  
#     def volume_annotation_count(request):
#         '''Total number of annotations for this volume; filtered by annotations
#         *visible* to a particular user, if specified.'''
#         notes = Annotation.objects.all()
#         current_user = request.user.id
#         volume_annotation_count = notes.filter(owner_id=current_user).count()
#         return volume_annotation_count

# TODO is this needed?
class Note(models.Model):
    label = models.CharField(max_length=255)
    language = models.CharField(max_length=10, default='en')
    manifest = models.ForeignKey(Manifest, null=True, on_delete=models.CASCADE)
