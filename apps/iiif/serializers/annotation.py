# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation"""
import json
from django.core.serializers import deserialize
from django.contrib.auth import get_user_model
from apps.iiif.serializers.base import Serializer as JSONSerializer
import config.settings.local as settings

USER = get_user_model()


class Serializer(JSONSerializer):
    """
    Serialize a :class:`apps.iiif.annotation.models.Annotation`
    object based on the IIIF Presentation API

    IIIF V2 Annotation List https://iiif.io/api/presentation/2.1/#annotation-list
    """

    def _init_options(self):
        super()._init_options()
        self.owners = self.json_kwargs.pop("owners", 0)

    def get_dump_object(self, obj):
        """
        Serialize an :class:`apps.iiif.annotation.models.Annotation`
        based on the IIIF presentation API

        :param obj: Annotation to be serialized.
        :type obj: :class:`apps.iiif.annotation.models.Annotation`
        :return: Serialized annotation.
        :rtype: dict
        """
        # TODO: Add more validation checks before trying to serialize.
        if (self.version == "v2") or (self.version is None):
            name = "OCR"
            if obj.owner_id:
                name = obj.owner.username if obj.owner.name == "" else obj.owner.name
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": str(obj.pk),
                "@type": "oa:Annotation",
                "motivation": obj.motivation,
                "annotatedBy": {"name": name},
                "resource": {
                    "@type": obj.resource_type,
                    "format": "text/html",
                    "chars": obj.content,
                    "language": obj.language,
                },
                "on": {
                    "full": "{h}/iiif/{v}/{m}/canvas/{c}".format(
                        h=settings.HOSTNAME,
                        v=self.version,
                        m=obj.canvas.manifest.pid,
                        c=obj.canvas.pid,
                    ),
                    "@type": "oa:SpecificResource",
                    "within": {
                        "@id": "{h}/iiif/{v}/{c}/manifest".format(
                            h=settings.HOSTNAME,
                            v=self.version,
                            c=obj.canvas.manifest.pid,
                        ),
                        "@type": "sc:Manifest",
                    },
                    "selector": {
                        "@type": "oa:FragmentSelector",
                        "value": f"xywh={obj.x},{obj.y},{obj.w},{obj.h}",
                    },
                },
            }
            if hasattr(obj, "style") and obj.style is not None:
                data["stylesheet"] = self.__serialize_style(obj)

            if obj.item is not None:
                data["on"]["selector"]["item"] = self.__serialize_item(obj)
            else:
                data["on"]["selector"]["item"] = {"@type": "oa:FragmentSelector"}

            if hasattr(obj, "tags") and obj.tags.exists():
                data["motivation"] = data["motivation"].split(",")
                data["resource"] = [data["resource"]]
                for tag in obj.tags.all():
                    wa_tag = {"@type": "oa:Tag", "chars": tag.name}
                    data["resource"].append(wa_tag)  # pylint: disable= no-member

            return data
        return None

        # TODO: write serializer for v3 of the IIIF Presentation API.
        # elif (self.version == 'v3'):
        #     return None

    # TODO: is this needed?
    @classmethod
    def __serialize_item(cls, obj):
        return obj.item

    @classmethod
    def __serialize_style(cls, obj):
        """
        Private function to serialize the stylesheet data.

        :param obj: Annotation to be serialized
        :type obj: :class:`apps.iiif.annotation.models.Annotation`
        :return: Stylesheet data compliant with the web annotation standard.
        :rtype: dict
        """
        return {"type": "CssStylesheet", "value": obj.style}


def Deserializer(data):
    """Deserialize IIIF Annotation"""

    if isinstance(data, str):
        data = json.loads(data)

    if "@context" in data and "2/context.json" in data["@context"]:
        return deserialize("annotation_v2", data)

    return deserialize("annotation_v3", data)


# def Deserializer(data):
#     if isinstance(data, str):
#         data = json.loads(data)

#     annotation = Annotation()
#     if "@type" in data and data["@type"] == "oa:Annotation":
#         if data["annotatedBy"]["name"] == "OCR":
#             data["annotatedBy"]["name"] = "ocr"
#             annotation.owner = USER.objects.get(username="ocr", name="OCR")
#         annotation.oa_annotation = data
#         annotation.resource_type = annotation.OCR
#         annotation.motivation = data["motivation"]
#         annotation.content = data["resource"]["chars"]
#         annotation.language = data["resource"]["language"]
#         annotation.canvas = Canvas.objects.get(pid=data["on"]["full"].split("/")[-1])
#         dimensions = data["on"]["selector"]["value"].split("=")[-1].split(",")
#         annotation.x, annotation.y, annotation.w, annotation.h = [
#             int(d) for d in dimensions
#         ]

#     elif "type" in data and data["type"] == "Annotation":
#         annotation.owner = USER.objects.get(username=data["body"][0]["creator"]["id"])
#         if annotation.owner.username == "ocr":
#             pass
#         else:
#             annotation = UserAnnotation(owner=annotation.owner)
#             annotation.canvas = Canvas.objects.get(
#                 pid=data["target"]["source"].split("/")[-1]
#             )

#             for body in data["body"]:
#                 if body["purpose"] == "commenting":
#                     annotation.content = body["value"]
#                 if body["purpose"] == "tagging":
#                     annotation.save()
#                     annotation.tags.add(body["value"])

#             if data["target"]["selector"]["type"] == "SvgSelector":
#                 annotation.svg = data["target"]["selector"]["value"]

#                 if (
#                     "refinedBy" in data["target"]["selector"]
#                     and data["target"]["selector"]["refinedBy"]["type"]
#                     == "FragmentSelector"
#                 ):
#                     annotation.x, annotation.y, annotation.w, annotation.h = [
#                         float(n)
#                         for n in data["target"]["selector"]["refinedBy"]["value"]
#                         .split("=")[-1]
#                         .split(",")
#                     ]

#             if data["target"]["selector"]["type"] == "FragmentSelector":
#                 annotation.x, annotation.y, annotation.w, annotation.h = [
#                     float(n)
#                     for n in data["target"]["selector"]["value"]
#                     .split(":")[-1]
#                     .split(",")
#                 ]

#             if data["target"]["selector"]["type"] == "RangeSelector":
#                 annotation.start_selector = Annotation.objects.get(
#                     id=findall(
#                         r"([A-Za-z0-9\-]+)",
#                         data["target"]["selector"]["startSelector"]["value"],
#                     )[-1]
#                 )
#                 annotation.end_selector = Annotation.objects.get(
#                     id=findall(
#                         r"([A-Za-z0-9\-]+)",
#                         data["target"]["selector"]["endSelector"]["value"],
#                     )[-1]
#                 )
#                 annotation.start_offset = data["target"]["selector"]["startSelector"][
#                     "refinedBy"
#                 ]["start"]
#                 annotation.end_offset = data["target"]["selector"]["endSelector"][
#                     "refinedBy"
#                 ]["end"]

#                 start_position = annotation.start_selector.order
#                 end_position = annotation.end_selector.order
#                 text = Annotation.objects.filter(
#                     canvas=annotation.canvas,
#                     order__lt=end_position,
#                     order__gte=start_position,
#                 ).order_by("order")

#                 try:
#                     annotation["x"] = min(text.values_list("x", flat=True))
#                     annotation["y"] = max(text.values_list("y", flat=True))
#                     annotation["h"] = max(text.values_list("h", flat=True))
#                     annotation["w"] = text.last().x + text.last().w - annotation["x"]
#                 except ValueError:
#                     pass

#     return annotation
