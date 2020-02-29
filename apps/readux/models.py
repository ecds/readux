from django.db import models
from apps.iiif.annotations.models import AbstractAnnotation, Annotation
from django.db.models import signals
from django.dispatch import receiver
from apps.iiif.canvases.models import Canvas
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase
import json
import re

class TaggedUserAnnotations(TaggedItemBase):
    content_object = models.ForeignKey('UserAnnotation', on_delete=models.CASCADE)

class UserAnnotation(AbstractAnnotation):
    COMMENTING = 'oa:commenting'
    PAINTING = 'sc:painting'
    TAGGING = '%s,oa:tagging' % COMMENTING
    MOTIVATION_CHOICES = (
        (COMMENTING, 'commenting'),
        (PAINTING, 'painting'),
        (TAGGING, 'tagging and commenting')
    )

    start_selector = models.ForeignKey(Annotation, on_delete=models.CASCADE, null=True, blank=True, related_name='start_selector', default=None)
    end_selector = models.ForeignKey(Annotation, on_delete=models.CASCADE, null=True, blank=True, related_name='end_selector', default=None)
    start_offset = models.IntegerField(null=True, blank=True, default=None)
    end_offset = models.IntegerField(null=True, blank=True, default=None)
    tags = TaggableManager(through=TaggedUserAnnotations)

    @property
    def item(self):
        if self.__is_text_annotation():
            return self.__text_anno_item()
        elif self.__is_svg_annotation():
            return self.__svg_anno_item()
        else:
            return None

    @property
    def tag_list(self):
        if self.tags.exists():
            return [tag.name for tag in self.tags.all()]
        else:
            return []

    def parse_mirador_annotation(self):
        # TODO: Should we use multiple motivations? 
        # if(type(self.oa_annotation.resource), list):
        #     self.motivation = self.TAGGING
        # else:
        #     self.motivation = AbstractAnnotation.COMMENTING
        self.motivation = AbstractAnnotation.COMMENTING

        if (type(self.oa_annotation) == str):
            self.oa_annotation = json.loads(self.oa_annotation)

        if isinstance(self.oa_annotation['on'], list):
            anno_on = self.oa_annotation['on'][0]
        elif isinstance(self.oa_annotation['on'], dict):
            anno_on = self.oa_annotation['on']

        if self.canvas == None:
            self.canvas = Canvas.objects.get(pid=anno_on['full'].split('/')[-1])

        mirador_item = anno_on['selector']['item']

        if (mirador_item['@type'] == 'oa:SvgSelector'):
            self.svg = mirador_item['value']
            self.__set_xywh_svg_anno()

        elif (mirador_item['@type'] == 'RangeSelector'):
            self.start_selector = Annotation.objects.get(pk=mirador_item['startSelector']['value'].split("'")[1])
            self.end_selector = Annotation.objects.get(pk=mirador_item['endSelector']['value'].split("'")[1])
            self.start_offset = mirador_item['startSelector']['refinedBy']['start']
            self.end_offset = mirador_item['endSelector']['refinedBy']['end']
            self.__set_xywh_text_anno()

        if isinstance(self.oa_annotation['resource'], dict):
            self.content = self.oa_annotation['resource']['chars']
            self.resource_type = self.oa_annotation['resource']['@type']
        elif isinstance(self.oa_annotation['resource'], list) and len(self.oa_annotation['resource']) == 1:
            self.content = self.oa_annotation['resource'][0]['chars']
            self.resource_type = self.oa_annotation['resource'][0]['@type']
            if self.tags.exists():
                for tag in self.tags.all():
                    self.tags.remove(tag.name)
        elif isinstance(self.oa_annotation['resource'], list) and len(self.oa_annotation['resource']) > 1:
            # Assume tags
            self.motivation = self.TAGGING
            incoming_tags = []
            # Get the tags from the incoming annotation.
            for resource in self.oa_annotation['resource']:
                # Set the non-tag resource
                if resource['@type'] == 'dctypes:Text':
                    self.content = resource['chars']
                    self.resource_type = resource['@type']
                elif resource['@type'] == 'oa:Tag': # and resource['chars'] not in self.tag_list:
                    # Add the tag to the annotation
                    self.tags.add(resource['chars'])
                    # Make a list of incoming tags to compare with list of saved tags.
                    incoming_tags.append(resource['chars'])
            
            # Check if any tags have been removed
            if len(self.tag_list) > 0:
                for existing_tag in self.tag_list:
                    if existing_tag not in incoming_tags:
                        self.tags.remove(existing_tag)
        
        # Replace the ID given by Mirador with the Readux given ID
        if ('stylesheet' in self.oa_annotation):
            uuid_pattern = re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}')
            self.style = uuid_pattern.sub(str(self.id), self.oa_annotation['stylesheet']['value'])

    def __is_text_annotation(self):
        return all([
            isinstance(self.end_offset, int),
            isinstance(self.start_offset, int),
            isinstance(self.start_selector, Annotation),
            isinstance(self.end_selector, Annotation)
        ])

    def __is_svg_annotation(self):
        return self.svg is not None

    def __set_xywh_text_anno(self):
        if (self.__is_text_annotation() is None):
            return None
        start_position = self.start_selector.order
        end_position = self.end_selector.order
        text = Annotation.objects.filter(
            canvas=self.canvas,
            order__lt=end_position,
            order__gte=start_position
        ).order_by('order')
        self.x = min(text.values_list('x', flat=True))
        self.y = max(text.values_list('y', flat=True))
        self.h = max(text.values_list('h', flat=True))
        self.w = text.last().x + text.last().w - self.x

    def __text_anno_item(self):
        return dict({
            "@type": "RangeSelector",
            "startSelector": {
                "@type": "XPathSelector",
                "value": "//*[@id='%s']" % str(self.start_selector.pk),
                "refinedBy" : {
                    "@type": "TextPositionSelector",
                    "start": self.start_offset
                }
            },
            "endSelector": {
                "@type": "XPathSelector",
                "value": "//*[@id='%s']" % str(self.end_selector.pk),
                "refinedBy" : {
                    "@type": "TextPositionSelector",
                    "end": self.end_offset
                }
            }
        })

    def __svg_anno_item(self):
        return dict({
            "@type": "oa:SvgSelector",
            "value": self.svg,
            "@type": "oa:Choice",
            "default": {
                "@type": "oa:FragmentSelector",
                "value": "xywh=%s,%s,%s,%s" % (str(self.x), str(self.y), str(self.w), str(self.h))
            }
        })

    def __set_xywh_svg_anno(self):
        dimensions = None
        if 'default' in self.oa_annotation['on'][0]['selector'].keys():
            dimensions = self.oa_annotation['on'][0]['selector']['default']['value'].split('=')[-1].split(',')
        # elif 'value' in self.oa_annotation['on'][0]['selector']['item'].keys():
        #     dimensions = self.oa_annotation['on'][0]['selector']['item']['value'].split('=')[-1].split(',')
        if dimensions is not None:
            self.x = dimensions[0]
            self.y = dimensions[1]
            self.w = dimensions[2]
            self.h = dimensions[3]

# TODO: Override the save method and move this there.
@receiver(signals.pre_save, sender=UserAnnotation)
def parse_payload(sender, instance, **kwargs):
    instance.parse_mirador_annotation()
