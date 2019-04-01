from django.db import models
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify 
import uuid

class Collection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    summary = models.TextField()
    pid = models.CharField(max_length=255, help_text="Do not use -'s or spaces in the pid.")
    attribution = models.CharField(max_length=255, null=True, help_text="Repository holding the collection")
    metadata = JSONField(null=True)
    upload = models.FileField(upload_to='uploads/', null=True)

    def __str__(self):
        return self.label
