from django.db import models
import uuid

class Volume(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  title = models.CharField(max_length=999)

  def __str__(self):
    return self.title
  
  class Meta:
    ordering = ('title',)

class Page(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
  page_number = models.IntegerField()

  def __str__(self):
    return self.page_number
  
  class Meta:
    ordering = ('page_number',)
  