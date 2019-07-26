from django.contrib.postgres.fields import JSONField
from django.db import models
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
import json
import uuid

# class Annotation(models.Model):
#     '''
#     Django database model to manage IIIF annotations generated by Mirador.
#     '''

#     #: regex for recognizing valid UUID, for use in site urls
#     # UUID_REGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'

#     #: annotation schema version: default v1.0
#     schema_version = "v1.0"
#     # for now, hard-coding until or unless we need to support more than
#     # one version of annotation

#     #: unique id for the annotation; uses :meth:`uuid.uuid4`
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     # data model includes version, do we need to set that in the db?
#     # "annotator_schema_version": "v1.0",        # schema version: default v1.0

#     #: datetime annotation was created; automatically set when added
#     created = models.DateTimeField(auto_now_add=True)
#     #: datetime annotation was last updated; automatically updated on save
#     updated = models.DateTimeField(auto_now=True)
#     #: content of the annotation
#     text = models.TextField()
#     #: the annotated text
#     quote = models.TextField(blank=False)
#     volume_identifier = models.TextField(blank=False)
#     page = models.TextField(blank=False)
#     #: URI of the annotated document
#     uri = models.URLField(blank=False)
#     #: user who owns the annotation
#     #: when serialized, id of annotation owner OR an object with an 'id' property
#     # Make user optional for now
#     # user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

#     #: Readux-specific field: URI for the volume that an annotation
#     #: is associated with (i.e., volume a page is part of)
#     volume_uri = models.URLField(blank=True)

#     # tags still todo
#     # "tags": [ "review", "error" ],             # list of tags (from Tags plugin)

#     #: any additional data included in the annotation not parsed into
#     #: specific model fields; this includes ranges, permissions,
#     #: annotation data, etc
#     oa_annotation = JSONField(default=dict, blank=False)

# class Meta:
#         # Translators: admin:skip
#         verbose_name = _('ANNOTATION.NAME.LABEL')
#         # Translators: admin:skip
#         verbose_name_plural = _('ANNOTATION.NAME.PLURAL')

#         # permissions = (
#         #     # ('add_collection', 'Can add new collection'),
#         #     # ('change_collection', 'Can change all data on any collection'),
#         #     # ('delete_collection', 'Can delete any collection'),
#         # )

class Annotation(models.Model):
    OCR = 'cnt:ContentAsText'
    TEXT = 'dctypes:Text'
    TYPE_CHOICES = (
        (OCR, 'ocr'),
        (TEXT, 'text')
    )
    
    COMMENTING = 'oa:commenting'
    PAINTING = 'sc:painting'
    MOTIVATION_CHOICES = (
        (COMMENTING, 'commeting'),
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
    svg = models.TextField(blank=True)

    ordering = ['order']

    def parse_oa_annotation(self):
        dimensions = self.oa_annotation['on'][0]['selector']['default']['value'].split('=')[-1].split(',')
        self.x = dimensions[0]
        self.y = dimensions[1]
        self.w = dimensions[2]
        self.h = dimensions[3]


    def __str__(self):
        return str(self.pk)

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
    else:
        if (type(instance.oa_annotation) == str):
            instance.oa_annotation = json.loads(instance.oa_annotation)
        instance.svg = instance.oa_annotation['on'][0]['selector']['item']['value']
        instance.oa_annotation['annotatedBy'] = {'name': 'Me'}
        instance.content = instance.oa_annotation['resource'][0]['chars']
        instance.resource_type = instance.oa_annotation['resource'][0]['@type']
        instance.parse_oa_annotation()

