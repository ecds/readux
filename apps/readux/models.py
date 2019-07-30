from django.db import models
from apps.iiif.annotations.models import AbstractAnnotation, Annotation
from django.db.models import signals
from django.dispatch import receiver
from apps.iiif.canvases.models import Canvas
import json

class UserAnnotation(AbstractAnnotation):
    start_selector = models.ForeignKey(Annotation, on_delete=models.CASCADE, null=True, related_name='start_selector', default=None)
    end_selector = models.ForeignKey(Annotation, on_delete=models.CASCADE, null=True, related_name='end_selector', default=None)
    start_offset = models.IntegerField(null=True, default=None)
    end_offset = models.IntegerField(null=True, default=None)

    @property
    def item(self):
        if self.__is_text_annotation():
            return self.__text_anno_item()
        elif self.__is_svg_annotation():
            return self.__svg_anno_item()
        else:
            return None

    def parse_mirador_annotation(self):
        print(self.oa_annotation)
        if (type(self.oa_annotation) == str):
            self.oa_annotation = json.loads(self.oa_annotation)

        anno_on = self.oa_annotation['on'][0]

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

        
        self.content = self.oa_annotation['resource'][0]['chars']
        self.resource_type = self.oa_annotation['resource'][0]['@type']

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

    def __set_xywh_svg_anno(self):
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
                    "start": self.end_offset
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


@receiver(signals.pre_save, sender=UserAnnotation)
def parse_payload(sender, instance, **kwargs):
    instance.parse_mirador_annotation()