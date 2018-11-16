from django.db import models
from ..kollections.models import Collection
from django.contrib.postgres.fields import JSONField
import uuid

class Manifest(models.Model):
    DIRECTIONS = (
        ('left-to-right', 'Left to Right'),
        ('right-to-left', 'Right to Left')
    )
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pid = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    summary = models.TextField()
    author = models.TextField(null=True)
    published_city = models.TextField(null=True)
    published_date = models.CharField(max_length=25)
    publisher = models.CharField(max_length=255)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    pdf = models.URLField()
    metadata = JSONField(default=dict, blank=False)
    viewingDirection = models.CharField(max_length=13, choices=DIRECTIONS, default="left-to-right")

    @property
    def note_list(self):
      self.note_set.values('label')[0]['label']

    @property
    def publisher_bib(self):
      "%s : %s" % (published_city, publisher)

    def __str__(self):
        return self.name

class Note(models.Model):
    label = models.CharField(max_length=255)
    language = models.CharField(max_length=10, default='en')
    manifest = models.ForeignKey(Manifest, null=True, on_delete=models.CASCADE)
