from django.db import models
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify
import uuid

class Collection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    summary = models.TextField()
    pid = models.CharField(max_length=255)
    metadata = JSONField(null=True)
    upload = models.FileField(upload_to='uploads/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.label
