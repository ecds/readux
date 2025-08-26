"""Django Models for Readux"""

import json
import re
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase
from django.db import models
from apps.iiif.annotations.models import AbstractAnnotation, Annotation
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.documents import ManifestDocument


class TaggedUserAnnotations(TaggedItemBase):
    """Model for tagging :class:`UserAnnotation`s using Django Taggit."""

    content_object = models.ForeignKey("UserAnnotation", on_delete=models.CASCADE)


class UserAnnotation(AbstractAnnotation):
    """Model for User Annotations."""

    COMMENTING = "oa:commenting"
    PAINTING = "sc:painting"
    TAGGING = f"{COMMENTING},oa:tagging"
    MOTIVATION_CHOICES = (
        (COMMENTING, "commenting"),
        (PAINTING, "painting"),
        (TAGGING, "tagging and commenting"),
    )

    start_selector = models.ForeignKey(
        Annotation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="start_selector",
        default=None,
    )
    end_selector = models.ForeignKey(
        Annotation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="end_selector",
        default=None,
    )
    start_offset = models.IntegerField(null=True, blank=True, default=None)
    end_offset = models.IntegerField(null=True, blank=True, default=None)
    tags = TaggableManager(through=TaggedUserAnnotations)

    @property
    def item(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        if self.__is_text_annotation():
            return self.__text_anno_item()
        if self.__is_svg_annotation():
            return self.__svg_anno_item()
        return None

    @property
    def tag_list(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        if self.tags.exists():
            return [tag.name for tag in self.tags.all()]
        return []

    def pre_save(self):
        """Prepare annotation to be saved."""
        if self.primary_selector == "RG":
            self.__xywh_text_anno()
        if isinstance(self.oa_annotation, str):
            self.oa_annotation = json.loads(self.oa_annotation)
        if "on" in self.oa_annotation.keys():
            self.parse_mirador_annotation()

    def post_save(self):
        """
        Finds tags in the oa_annotation and applies them to
        the annotation.
        """
        if self.motivation == self.TAGGING:
            incoming_tags = []
            # Get the tags from the incoming annotation.
            tags = [
                res
                for res in self.oa_annotation["resource"]
                if res["@type"] == "oa:Tag"
            ]
            for tag in tags:
                # Add the tag to the annotation
                self.tags.add(tag["chars"])
                # Make a list of incoming tags to compare with list of saved tags.
                incoming_tags.append(tag["chars"])

            # Check if any tags have been removed
            if len(self.tag_list) > 0:
                for existing_tag in self.tag_list:
                    if existing_tag not in incoming_tags:
                        self.tags.remove(existing_tag)

    def save(self, *args, **kwargs):
        self.pre_save()
        if self.canvas:
            index = ManifestDocument()
            index.update(self.canvas.manifest, True, "index")
        super().save(*args, **kwargs)
        self.post_save()

    def delete(self, *args, **kwargs):
        if self.canvas:
            index = ManifestDocument()
            index.update(self.canvas.manifest, True, "delete")
        super().delete(*args, **kwargs)

    def update(self, attrs=None, tags=None):
        """Method to update an annotation object with a dict of attributes and a list of tags

        :param attrs: _description_, defaults to None
        :type attrs: dict, optional
        :param tags: _description_, defaults to None
        :type tags: list, optional
        """
        if isinstance(attrs, dict):
            for attr, value in attrs.items():
                setattr(self, attr, value)

        if isinstance(tags, list):
            self.tags.clear()
            for tag in tags:
                self.tags.add(tag)

        self.save()

    def parse_mirador_annotation(self):
        """DEPRECATED
        Parses annotation from mirador
        """
        self.motivation = AbstractAnnotation.OA_COMMENTING

        anno_on = None

        if isinstance(self.oa_annotation["on"], list):
            anno_on = self.oa_annotation["on"][0]
        elif isinstance(self.oa_annotation["on"], dict):
            anno_on = self.oa_annotation["on"]

        if self.canvas is None and anno_on is not None:
            self.canvas = Canvas.objects.get(pid=anno_on["full"].split("/")[-1])

        mirador_item = anno_on["selector"]["item"]

        if mirador_item["@type"] == "oa:SvgSelector":
            self.svg = mirador_item["value"]
            self.__set_xywh_svg_anno()

        elif mirador_item["@type"] == "RangeSelector":
            self.start_selector = Annotation.objects.get(
                pk=mirador_item["startSelector"]["value"].split("'")[1]
            )
            self.end_selector = Annotation.objects.get(
                pk=mirador_item["endSelector"]["value"].split("'")[1]
            )
            self.start_offset = mirador_item["startSelector"]["refinedBy"]["start"]
            self.end_offset = mirador_item["endSelector"]["refinedBy"]["end"]
            self.__xywh_text_anno()

        if isinstance(self.oa_annotation["resource"], dict):
            self.content = self.oa_annotation["resource"]["chars"]
            self.resource_type = self.oa_annotation["resource"]["@type"]
        elif (
            isinstance(self.oa_annotation["resource"], list)
            and len(self.oa_annotation["resource"]) == 1
        ):
            self.content = self.oa_annotation["resource"][0]["chars"]
            self.resource_type = self.oa_annotation["resource"][0]["@type"]
            # Assume all tags have been removed.
            if self.tags.exists():
                self.tags.clear()
        elif (
            isinstance(self.oa_annotation["resource"], list)
            and len(self.oa_annotation["resource"]) > 1
        ):
            # Assume tagging
            self.motivation = self.TAGGING
            text = [
                res
                for res in self.oa_annotation["resource"]
                if res["@type"] == "dctypes:Text"
            ]
            self.content = text[0]["chars"]

        # Replace the ID given by Mirador with the Readux given ID
        if "stylesheet" in self.oa_annotation:
            uuid_pattern = re.compile(
                r"[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}"
            )
            self.style = uuid_pattern.sub(
                str(self.id), self.oa_annotation["stylesheet"]["value"]
            )

        return True

    def __is_text_annotation(self):
        """Check if annotation is for text.

        :return: True if annotation is for text.
        :rtype: bool
        """
        return all(
            [
                isinstance(self.end_offset, int),
                isinstance(self.start_offset, int),
                isinstance(self.start_selector, Annotation),
                isinstance(self.end_selector, Annotation),
            ]
        )

    def __is_svg_annotation(self):
        """Check if annotation is for image region.

        :return: True if annotation is for image region.
        :rtype: bool
        """
        return self.svg is not None

    def __xywh_text_anno(self):
        start_position = self.start_selector.order
        end_position = self.end_selector.order
        text = None
        if self.start_selector == self.end_selector:
            text = Annotation.objects.filter(id=str(self.start_selector.id))
        else:
            text = Annotation.objects.filter(
                canvas=self.canvas, order__lte=end_position, order__gte=start_position
            ).order_by("order")
        self.x = min(text.values_list("x", flat=True))
        self.y = min(text.values_list("y", flat=True))
        far_y_anno = text.order_by("y").last()
        self.h = far_y_anno.y + far_y_anno.h - self.y
        far_x_anno = text.order_by("x").last()
        self.w = far_x_anno.x + far_x_anno.w - self.x
        # self.w = max([anno.x + anno.w for anno in text]) - self.x
        # self.h = max([anno.y + anno.h for anno in text]) - self.y

    def __text_anno_item(self):
        return dict(
            {
                "@type": "RangeSelector",
                "startSelector": {
                    "@type": "XPathSelector",
                    "value": f"//*[@id='{str(self.start_selector.pk)}']",
                    "refinedBy": {
                        "@type": "TextPositionSelector",
                        "start": self.start_offset,
                    },
                },
                "endSelector": {
                    "@type": "XPathSelector",
                    "value": f"//*[@id='{str(self.end_selector.pk)}']",
                    "refinedBy": {
                        "@type": "TextPositionSelector",
                        "end": self.end_offset,
                    },
                },
            }
        )

    def __svg_anno_item(self):
        # pylint: disable=duplicate-key
        return dict(
            {
                "@type": "oa:SvgSelector",
                "value": self.svg,
                "@type": "oa:SvgSelector",
                "default": {
                    "@type": "oa:FragmentSelector",
                    "value": f"xywh={str(self.x)},{str(self.y)},{str(self.w)},{str(self.h)}",
                },
            }
        )
        # pylint: enable=duplicate-key

    def __set_xywh_svg_anno(self):
        dimensions = None
        if "default" in self.oa_annotation["on"][0]["selector"].keys():
            dimensions = (
                self.oa_annotation["on"][0]["selector"]["default"]["value"]
                .split("=")[-1]
                .split(",")
            )
        if dimensions is not None:
            self.x = dimensions[0]
            self.y = dimensions[1]
            self.w = dimensions[2]
            self.h = dimensions[3]
