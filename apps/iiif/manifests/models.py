from django.db import models
import config.settings.local as settings
from ..kollections.models import Collection
from django.contrib.postgres.fields import JSONField
from modelcluster.models import ClusterableModel
from wagtailautocomplete.edit_handlers import AutocompletePanel
from json import JSONEncoder
import uuid
from uuid import UUID
#trying to work with autocomplete
JSONEncoder_olddefault = JSONEncoder.default
def JSONEncoder_newdefault(self, o):
    if isinstance(o, UUID): return str(o)
    return JSONEncoder_olddefault(self, o)
JSONEncoder.default = JSONEncoder_newdefault

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
    #collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name = 'manifest')
    collections = models.ManyToManyField(Collection, related_name = 'manifests')
    pdf = models.URLField()
    metadata = JSONField(default=dict, blank=False)
    viewingDirection = models.CharField(max_length=13, choices=DIRECTIONS, default="left-to-right")
    created_at = models.DateTimeField(auto_now_add=True)
    #starting_page = models.ForeignKey('canvases.Canvas', related_name="first", on_delete=models.SET_NULL, null=True, blank=True, help_text="Choose the page that will show on loading.")
    autocomplete_search_field = 'label'

    @property
    def note_list(self):
      self.note_set.values('label')[0]['label']

    @property
    def publisher_bib(self):
      "%s : %s" % (published_city, publisher)

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

class Note(models.Model):
    label = models.CharField(max_length=255)
    language = models.CharField(max_length=10, default='en')
    manifest = models.ForeignKey(Manifest, null=True, on_delete=models.CASCADE)
