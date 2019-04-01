from django.db import models
from ..kollections.models import Collection
from django.contrib.postgres.fields import JSONField
import uuid

class Manifest(models.Model):
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


    @property
    def note_list(self):
      self.note_set.values('label')[0]['label']

    @property
    def publisher_bib(self):
      "%s : %s" % (published_city, publisher)

    def __str__(self):
        return self.label

class Note(models.Model):
    label = models.CharField(max_length=255)
    language = models.CharField(max_length=10, default='en')
    manifest = models.ForeignKey(Manifest, null=True, on_delete=models.CASCADE)
