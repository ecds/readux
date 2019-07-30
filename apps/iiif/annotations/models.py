from django.contrib.postgres.fields import JSONField
from django.db import models
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
import json
import uuid
from abc import abstractmethod

class AbstractAnnotation(models.Model):
    OCR = 'cnt:ContentAsText'
    TEXT = 'dctypes:Text'
    TYPE_CHOICES = (
        (OCR, 'ocr'),
        (TEXT, 'text')
    )
    
    COMMENTING = 'oa:commenting'
    PAINTING = 'sc:painting'
    MOTIVATION_CHOICES = (
        (COMMENTING, 'commenting'),
        (PAINTING, 'painting')
    )

    PLAIN = 'text/plain'
    HTML = 'text/html'
    FORMAT_CHOICES = (
        (PLAIN, 'plain text'),
        (HTML, 'html')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    x = models.IntegerField()
    y = models.IntegerField()
    w = models.IntegerField()
    h = models.IntegerField()
    order = models.IntegerField(default=0)
    content = models.CharField(max_length=1000)
    resource_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=TEXT)
    motivation = models.CharField(max_length=50, choices=MOTIVATION_CHOICES, default=PAINTING)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=PLAIN)
    canvas = models.ForeignKey('canvases.Canvas', on_delete=models.CASCADE, null=True)
    language = models.CharField(max_length=10, default='en')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    oa_annotation = JSONField(default=dict, blank=False)
    # TODO Should we keep this for annotations from Mirador, or just get rid of it?
    svg = models.TextField()
    item = None

    ordering = ['order']

    # @property
    # @abstractmethod
    # def item(self):
    #     pass


    def parse_mirador_annotation(self):
        dimensions = None
        if 'default' in self.oa_annotation['on'][0]['selector'].keys():
            dimensions = self.oa_annotation['on'][0]['selector']['default']['value'].split('=')[-1].split(',')
        elif 'value' in self.oa_annotation['on'][0]['selector']['item'].keys():
            dimensions = self.oa_annotation['on'][0]['selector']['item']['value'].split('=')[-1].split(',')
        if dimensions is not None:
            self.x = dimensions[0]
            self.y = dimensions[1]
            self.w = dimensions[2]
            self.h = dimensions[3]


    def __str__(self):
        return str(self.pk)
    
    class Meta:
        abstract = True

class Annotation(AbstractAnnotation):
    class Meta:
        ordering = ['order']
        abstract = False

@receiver(signals.pre_save, sender=Annotation)
def set_span_element(sender, instance, **kwargs):
    if instance.resource_type in (sender.OCR,):
        try:
            instance.oa_annotation['annotatedBy'] = {'name': 'ocr'}
            # instance.svg = "<svg xmlns='http://www.w3.org/2000/svg' id='{pk}' class='ocrtext' fill=red' style='height: {h}px;' viewBox='0 0 {w} {h}'><text x='0' y='100%' textLength='100%' style='font-size: {h}px; user-select: all;'>{content}</text></svg>".format(pk=instance.pk, h=str(instance.h), w=str(instance.w), content=instance.content)
            # (12*(17.697/1.618))/12
            character_count = len(instance.content)
            font_size = (character_count*(instance.h/1.618))/character_count
            instance.content = "<span id='{pk}' style='font-family: monospace; height: {h}px; width: {w}px; font-size: {f}px'>{content}</span>".format(pk=instance.pk, h=str(instance.h), w=str(instance.w), content=instance.content, f=str(font_size))
        except ValueError as error:
            instance.content = ""
            print("WARNING: {e}".format(e=error))
    elif instance.oa_annotation == '{"annotatedBy": {"name": "ocr"}}': 
    #To do: refactor this code to better handle ingest. This elif allows for an admin to use import-export by defining oa_annotation as above to import ocr from a spreadsheet.
        try:
            #instance.oa_annotation['annotatedBy'] = {'name': 'ocr'}
            # instance.svg = "<svg xmlns='http://www.w3.org/2000/svg' id='{pk}' class='ocrtext' fill=red' style='height: {h}px;' viewBox='0 0 {w} {h}'><text x='0' y='100%' textLength='100%' style='font-size: {h}px; user-select: all;'>{content}</text></svg>".format(pk=instance.pk, h=str(instance.h), w=str(instance.w), content=instance.content)
            # (12*(17.697/1.618))/12
            character_count = len(instance.content)
            font_size = (character_count*(instance.h/1.618))/character_count
            instance.content = "<span id='{pk}' style='font-family: monospace; height: {h}px; width: {w}px; font-size: {f}px'>{content}</span>".format(pk=instance.pk, h=str(instance.h), w=str(instance.w), content=instance.content, f=str(font_size))
        except ValueError as error:
            instance.content = ""
            print("WARNING: {e}".format(e=error))

