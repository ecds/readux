import json
import uuid
from cssutils import parseString
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.serializers import serialize
from django.test import TestCase, Client
from django.test import RequestFactory
from apps import readux
from apps.iiif.manifests.models import Manifest
from apps.readux.views import ExportOptions, AnnotationCount
from ..annotations import Annotations, AnnotationCrud, AnnotationCountByCanvas
from ..models import UserAnnotation
from ..context_processors import current_version

User = get_user_model()


class AnnotationTests(TestCase):
    fixtures = [
        "users.json",
        "kollections.json",
        "manifests.json",
        "canvases.json",
        "annotations.json",
    ]

    valid_mirador_annotations = {
        "svg": {
            "oa_annotation": """{
            "on": [{
                "full": "https://readux-dev.org:3000/iiif/readux:st7r6/canvas/fedora:emory:5622",
                "@type": "oa:SpecificResource",
                "selector": {
                        "@type": "oa:Choice",
                        "item": {
                            "@type": "oa:SvgSelector",
                            "value": "<svg></svg>"
                        },
                    "default": {
                        "@type": "oa:FragmentSelector",
                        "value": "xywh=535,454,681,425"
                    }
                },
                "within": {
                    "@type": "sc:Manifest",
                    "@id": "https://ecds.emory.edu/iiif/MSS_Vat.lat.3225/manifest.json"
                }
            }],
            "@type": "oa:Annotation",
            "@context": "http://iiif.io/api/presentation/2/context.json",
            "@id": "13d3b867-d668-4294-b56a-df3e8860016c",
            "annotatedBy": {
                "name": "Me"
            },
            "resource": [{
                "format": "text/html",
                "@type": "dctypes:Text",
                "chars": "<p>wfv3v3v3</p>"
            }],
            "motivation": ["oa:commenting"]
        }"""
        },
        "text": {
            "oa_annotation": """{
                "@type": "oa:Annotation",
                "motivation": ["oa:commenting"],
                "annotatedBy": {
                    "name": "Me"
                },
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "resource": [{
                    "chars": "<p>mcoewmewom</p>",
                    "format": "text/html",
                    "@type": "dctypes:Text"
                }],
                "stylesheet": {
                    "value": ".anno-049e4a47-1d9e-4d52-8d30-fb9047d34481 { background: rgba(0, 128, 0, 0.5); }",
                    "type": "CssStylesheet"
                },
                "on": [{
                    "full": "https://readux-dev.org:3000/iiif/readux:st7r6/canvas/fedora:emory:5622",
                    "@type": "oa:SpecificResource",
                    "selector": {
                        "item": {
                            "@type": "RangeSelector",
                            "endSelector": {
                                "@type": "XPathSelector",
                                "value": "//*[@id='f842fe71-e1da-49c3-865e-f3e62a5179ff']",
                                "refinedBy": {
                                    "@type": "TextPositionSelector",
                                    "end": 2
                                }
                            },
                            "value": "xywh=2971,453,28,39",
                            "startSelector": {
                                "@type": "XPathSelector",
                                "value": "//*[@id='f846587c-1e1c-44d3-b1ce-20c0f7104dc5']",
                                "refinedBy": {
                                    "@type": "TextPositionSelector",
                                    "start": 0
                                }
                            }
                        },
                        "@type": "oa:FragmentSelector"
                    },
                    "within": {
                    "@type": "sc:Manifest",
                    "@id": "https://readux-dev.org:3000/iiif/v2/readux:st7r6/manifest"
                    }
                }]
            }"""
        },
        "tag": {
            "oa_annotation": """{
                "@type": "oa:Annotation",
                "motivation": ["oa:commenting"],
                "annotatedBy": {
                    "name": "Me"
                },
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "resource": [
                    {
                        "chars": "<p>mcoewmewom</p>",
                        "format": "text/html",
                        "@type": "dctypes:Text"
                    },
                    {
                        "@type": "oa:Tag",
                        "chars": "tag"
                    },
                    {
                        "@type": "oa:Tag",
                        "chars": "other tag"
                    }
                ],
                "stylesheet": {
                    "value": ".anno-049e4a47-1d9e-4d52-8d30-fb9047d34481 { background: rgba(0, 128, 0, 0.5); }",
                    "type": "CssStylesheet"
                },
                "on": [{
                    "full": "https://readux-dev.org:3000/iiif/readux:st7r6/canvas/fedora:emory:5622",
                    "@type": "oa:SpecificResource",
                    "selector": {
                        "item": {
                            "@type": "RangeSelector",
                            "endSelector": {
                                "@type": "XPathSelector",
                                "value": "//*[@id='f842fe71-e1da-49c3-865e-f3e62a5179ff']",
                                "refinedBy": {
                                    "@type": "TextPositionSelector",
                                    "end": 2
                                }
                            },
                            "value": "xywh=2971,453,28,39",
                            "startSelector": {
                                "@type": "XPathSelector",
                                "value": "//*[@id='f846587c-1e1c-44d3-b1ce-20c0f7104dc5']",
                                "refinedBy": {
                                    "@type": "TextPositionSelector",
                                    "start": 0
                                }
                            }
                        },
                        "@type": "oa:FragmentSelector"
                    },
                    "within": {
                    "@type": "sc:Manifest",
                    "@id": "https://readux-dev.org:3000/iiif/v2/readux:st7r6/manifest"
                    }
                }]
            }"""
        },
    }

    def setUp(self):
        # fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
        self.user_a = get_user_model().objects.get(pk=111)
        self.user_b = get_user_model().objects.get(pk=222)
        self.factory = RequestFactory()
        self.client = Client()
        self.view = Annotations.as_view()
        # self.volume_list_view = VolumeList.as_view()
        self.crud_view = AnnotationCrud.as_view()
        self.manifest = Manifest.objects.get(pk="464d82f6-6ae5-4503-9afc-8e3cdd92a3f1")
        self.canvas = self.manifest.canvas_set.all().first()
        self.collection = self.manifest.collections.first()

    def create_user_annotations(self, count, user):
        for _ in range(count):
            text_anno = UserAnnotation(
                oa_annotation=json.loads(
                    self.valid_mirador_annotations["text"]["oa_annotation"]
                ),
                owner=user,
            )
            text_anno.save()

    def load_anno(self, response):
        annotation_list = json.loads(response.content.decode("UTF-8-sig"))
        if "resources" in annotation_list:
            return annotation_list["resources"]
        else:
            return annotation_list

    def rando_anno(self):
        return UserAnnotation.objects.order_by("?").first()

    def test_get_user_annotations_unauthenticated(self):
        self.create_user_annotations(5, self.user_a)
        kwargs = {
            "username": "readux",
            "volume": self.manifest.pid,
            "canvas": self.canvas.pid,
        }
        url = reverse("user_annotations", kwargs=kwargs)
        response = self.client.get(url)
        assert response.status_code == 404
        kwargs = {
            "username": self.user_a.username,
            "volume": "readux:st7r6",
            "canvas": "fedora:emory:5622",
        }
        url = reverse("user_annotations", kwargs=kwargs)
        response = self.client.get(url)
        # annotation = self.load_anno(response)
        assert response.status_code == 401
        # assert len(annotation) == 0

    def test_user_annotation_count_by_canvas(self):
        self.create_user_annotations(5, self.user_a)
        kwargs = {"username": self.user_a.username, "manifest": self.manifest.pid}
        url = reverse("annotation_count_by_canvas", kwargs=kwargs)
        request = self.factory.get(url)
        request.user = self.user_a
        view = AnnotationCountByCanvas.as_view()
        response = view(
            request,
            username=self.user_a.username,
            manifest=self.manifest.pid,
        )
        response_data = json.loads(response.content.decode("UTF-8-sig"))
        assert response_data[0]["count"] == 5

    def test_mirador_svg_annotation_creation(self):
        request = self.factory.post(
            "/annotations-crud/",
            data=json.dumps(self.valid_mirador_annotations["svg"]),
            content_type="application/json",
        )
        request.user = self.user_a
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert annotation["body"][0]["creator"]["name"] == "Zaphod Beeblebrox"
        # assert annotation['on']['selector']['value'] == 'xywh=535,454,681,425'
        assert response.status_code == 201
        annotation_object = UserAnnotation.objects.get(
            pk=annotation["id"].replace("#", "")
        )
        assert annotation_object.x == 535
        assert annotation_object.y == 454
        assert annotation_object.w == 681
        assert annotation_object.h == 425

    def test_mirador_text_annotation_creation(self):
        request = self.factory.post(
            "/annotations-crud/",
            data=json.dumps(self.valid_mirador_annotations["text"]),
            content_type="application/json",
        )
        request.user = self.user_a
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert annotation["body"][0]["creator"]["name"] == "Zaphod Beeblebrox"
        # assert annotation['on']['selector']['value'] == 'xywh=468,2844,479,83'
        # assert re.match(r"http.*iiif/v2/readux:st7r6/canvas/fedora:emory:5622", annotation['on']['full'])
        assert response.status_code == 201

    def test_creating_annotation_from_string(self):
        request = self.factory.post(
            "/annotations-crud/",
            data=self.valid_mirador_annotations["text"],
            content_type="application/json",
        )
        request.user = self.user_a
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert annotation["body"][0]["creator"]["name"] == "Zaphod Beeblebrox"
        # assert annotation['on']['selector']['value'] == 'xywh=468,2844,479,83'
        # assert re.match(r"http.*iiif/v2/readux:st7r6/canvas/fedora:emory:5622", annotation['on']['full'])
        assert response.status_code == 201

    def test_get_user_annotations(self):
        self.create_user_annotations(4, self.user_a)
        kwargs = {
            "username": self.user_a.username,
            "volume": self.manifest.pid,
            "canvas": self.canvas.pid,
        }
        url = reverse("user_annotations", kwargs=kwargs)
        request = self.factory.get(url)
        request.user = self.user_a
        response = self.view(
            request,
            username=self.user_a.username,
            volume=self.manifest.pid,
            canvas=self.canvas.pid,
        )
        annotation = self.load_anno(response)
        assert len(annotation) == 4
        assert response.status_code == 200

    def test_get_only_users_user_annotations(self):
        self.create_user_annotations(5, self.user_b)
        self.create_user_annotations(4, self.user_a)
        kwargs = {
            "username": "marvin",
            "volume": self.manifest.pid,
            "canvas": self.canvas.pid,
        }
        url = reverse("user_annotations", kwargs=kwargs)
        request = self.factory.get(url)
        request.user = self.user_b
        response = self.view(
            request,
            username=self.user_b.username,
            volume=self.manifest.pid,
            canvas=self.canvas.pid,
        )
        annotation = self.load_anno(response)
        assert len(annotation) == 5
        assert response.status_code == 200
        assert len(UserAnnotation.objects.all()) == 9
        kwargs = {
            "username": self.user_a.username,
            "volume": "readux:st7r6",
            "canvas": "fedora:emory:5622",
        }
        url = reverse("user_annotations", kwargs=kwargs)
        response = self.client.get(url)
        annotation = self.load_anno(response)
        assert response.status_code == 401

    #        assert len(annotation) == 0

    def test_update_user_annotation(self):
        self.create_user_annotations(1, self.user_a)
        existing_anno = UserAnnotation.objects.all()[0]
        data = json.loads(self.valid_mirador_annotations["svg"]["oa_annotation"])
        data["@id"] = str(existing_anno.id)
        data = {"oa_annotation": data}
        resource = data["oa_annotation"]["resource"][0]
        resource["chars"] = "updated annotation"
        data["oa_annotation"]["resource"] = resource
        data["id"] = str(existing_anno.id)
        request = self.factory.put(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        request.user = self.user_a
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert response.status_code == 200
        assert annotation["body"][0]["value"] == "updated annotation"

    def test_update_non_existing_user_annotation(self):
        self.create_user_annotations(1, self.user_a)
        data = json.loads(self.valid_mirador_annotations["svg"]["oa_annotation"])
        new_id = str(uuid.uuid4())
        data["@id"] = new_id
        data["id"] = new_id
        request = self.factory.put(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        request.user = self.user_a
        response = self.crud_view(request)
        assert response.status_code == 404

    def test_update_someone_elses_annotation(self):
        self.create_user_annotations(4, self.user_a)
        rando_anno = self.rando_anno()
        data = {"id": str(rando_anno.pk)}
        request = self.factory.put(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        request.user = self.user_b
        response = self.crud_view(request)
        assert response.status_code == 401

    def test_updating_annotation_unauthenticated(self):
        self.create_user_annotations(1, self.user_a)
        existing_anno = UserAnnotation.objects.all()[0]
        data = json.loads(self.valid_mirador_annotations["svg"]["oa_annotation"])
        data["@id"] = str(existing_anno.id)
        data = {"oa_annotation": data}
        resource = data["oa_annotation"]["resource"][0]
        data["oa_annotation"]["resource"] = resource
        data["id"] = str(existing_anno.id)
        request = self.factory.put(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 401
        assert message["message"] == "You are not the owner of this annotation."

    def test_delete_user_annotation_as_owner(self):
        self.create_user_annotations(1, self.user_a)
        data = {"id": str(uuid.uuid4())}
        request = self.factory.delete(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        request.user = self.user_a
        response = self.crud_view(request)
        assert response.status_code == 404

    def test_delete_non_existant_user_annotation(self):
        self.create_user_annotations(1, self.user_a)
        existing_anno = UserAnnotation.objects.all()[0]
        data = {"id": str(existing_anno.pk)}
        request = self.factory.delete(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        request.user = self.user_a
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 204
        assert len(UserAnnotation.objects.all()) == 0

    def test_delete_someone_elses_annotation(self):
        self.create_user_annotations(1, self.user_a)
        rando_anno = self.rando_anno()
        data = {"id": str(rando_anno.pk)}
        request = self.factory.delete(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        request.user = self.user_b
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 401
        assert message["message"] == "You are not the owner of this annotation."

    def test_delete_annotation_unauthenticated(self):
        self.create_user_annotations(1, self.user_a)
        rando_anno = self.rando_anno()
        data = {"id": str(rando_anno.pk)}
        request = self.factory.delete(
            "/annotations-crud/", data=json.dumps(data), content_type="application/json"
        )
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 401
        assert message["message"] == "You are not the owner of this annotation."

    def test_user_annotations_on_canvas(self):
        # fetch a manifest with no user annotations
        kwargs = {"manifest": self.manifest.pid, "pid": self.canvas.pid}
        url = reverse("RenderCanvasDetail", kwargs=kwargs)
        response = self.client.get(url, data=kwargs)
        serialized_canvas = json.loads(response.content.decode("UTF-8-sig"))
        assert len(serialized_canvas["otherContent"]) == 1

        # add annotations to the manifest
        self.create_user_annotations(1, self.user_a)
        self.create_user_annotations(2, self.user_b)
        existing_anno_a = UserAnnotation.objects.all()[0]
        assert self.canvas.identifier == existing_anno_a.canvas.identifier
        existing_anno_b = UserAnnotation.objects.all()[2]
        assert self.canvas.identifier == existing_anno_b.canvas.identifier

        # fetch a manifest with annotations by two users
        response = self.client.get(url)
        serialized_canvas = json.loads(response.content.decode("UTF-8-sig"))
        assert response.status_code == 200
        assert serialized_canvas["@id"] == self.canvas.identifier
        assert serialized_canvas["label"] == str(self.canvas.position)
        assert len(serialized_canvas["otherContent"]) == 1

    def test_collection_detail_view_sort_and_order(self):
        descrizione = self.collection.manifests.first()
        vol2 = Manifest.objects.create(
            pid="test1", author="xyz", label="zyx", published_date_edtf="1000"
        )
        self.collection.manifests.add(vol2)
        url = reverse("collection", kwargs={"collection": self.collection.pid})

        # test all different sort options: title
        kwargs = {"sort": "title", "order": "asc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == descrizione.pid
        kwargs = {"sort": "title", "order": "desc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == vol2.pid

        # author
        kwargs = {"sort": "author", "order": "asc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == descrizione.pid
        kwargs = {"sort": "author", "order": "desc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == vol2.pid

        # edtf date published
        kwargs = {"sort": "date", "order": "asc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == vol2.pid
        # the other one doesn't have an edtf published date, so it should be sorted last
        # (nulls last) and therefore vol2 should still be first
        kwargs = {"sort": "date", "order": "desc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == vol2.pid

        # date added
        kwargs = {"sort": "added", "order": "asc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == descrizione.pid
        kwargs = {"sort": "added", "order": "desc"}
        response = self.client.get(url, data=kwargs)
        context = response.context_data
        assert context["volumes"][0].pid == vol2.pid

    def test_collection_detail_view_with_no_sort_or_order_specified(self):
        descrizione = self.collection.manifests.first()
        vol2 = Manifest.objects.create(
            pid="test1", author="xyz", label="zyx", published_date_edtf="1000"
        )
        self.collection.manifests.add(vol2)
        url = reverse("collection", kwargs={"collection": self.collection.pid})
        response = self.client.get(url)
        context = response.context_data
        # should order by title, asc
        assert context["volumes"][0].pid == descrizione.pid
        assert context["volumes"][1].pid == vol2.pid

    def test_volume_detail_view(self):
        url = reverse("volume", kwargs={"volume": self.manifest.pid})
        response = self.client.get(url)
        assert response.context_data["volume"] == self.manifest

    def test_export_options_view(self):
        kwargs = {"volume": self.manifest.pid}
        url = reverse("export", kwargs=kwargs)
        request = self.factory.get(url)
        request.user = self.user_a
        response = ExportOptions.as_view()(
            request, username=self.user_a.username, volume=self.manifest.pid
        )
        assert response.status_code == 200

    def test_motivation_is_commeting_by_default(self):
        self.create_user_annotations(1, self.user_a)
        anno = UserAnnotation.objects.all().first()
        assert anno.motivation == "oa:commenting"

    def test_style_attribute_adds_id_to_class_selector(self):
        self.create_user_annotations(1, self.user_a)
        anno = UserAnnotation.objects.all().first()
        assert str(anno.id) in anno.style

    def test_style_attribute_is_valid_css(self):
        self.create_user_annotations(1, self.user_a)
        anno = UserAnnotation.objects.all().first()
        style = parseString(anno.style)
        assert style.cssRules[0].valid

    def test_stylesheet_is_serialized(self):
        self.create_user_annotations(1, self.user_a)
        kwargs = {
            "username": self.user_a.username,
            "volume": self.manifest.pid,
            "canvas": self.canvas.pid,
        }
        url = reverse("user_annotations", kwargs=kwargs)
        request = self.factory.get(url)
        request.user = self.user_a
        response = self.view(
            request,
            username=self.user_a.username,
            volume=self.manifest.pid,
            canvas=self.canvas.pid,
        )
        annotation = self.load_anno(response)[0]
        assert "stylesheet" in annotation
        assert "value" in annotation["stylesheet"]
        assert "type" in annotation["stylesheet"]
        assert annotation["@id"] in annotation["stylesheet"]["value"]
        assert annotation["stylesheet"]["type"] == "CssStylesheet"

    def test_annotation_creation_with_tags(self):
        self.create_user_annotations(1, self.user_a)
        anno = UserAnnotation.objects.all().first()
        anno.oa_annotation = json.loads(
            self.valid_mirador_annotations["tag"]["oa_annotation"]
        )
        anno.save()
        assert anno.tags.exists()
        assert anno.tags.count() == 2
        assert anno.motivation == UserAnnotation.TAGGING
        assert anno.content == "<p>mcoewmewom</p>"
        assert "tag" in anno.tag_list
        assert "other tag" in anno.tag_list

    def test_updating_annotation_with_tags(self):
        self.create_user_annotations(1, self.user_a)
        anno = UserAnnotation.objects.all().first()
        anno.oa_annotation = json.loads(
            self.valid_mirador_annotations["tag"]["oa_annotation"]
        )
        anno.save()
        anno.oa_annotation = json.loads(serialize("annotation", [anno]))
        anno.save()
        anno = UserAnnotation.objects.get(pk=anno.pk)
        assert anno.tags.count() == 2

    def test_deleting_tags(self):
        self.create_user_annotations(1, self.user_a)
        anno = UserAnnotation.objects.all().first()
        anno.oa_annotation = json.loads(
            self.valid_mirador_annotations["tag"]["oa_annotation"]
        )
        anno.save()
        assert anno.tags.count() == 2
        assert len(anno.oa_annotation["resource"]) == 3
        # Remove one tag
        for index, resource in enumerate(anno.oa_annotation["resource"]):
            if resource["@type"] == "oa:Tag":
                del anno.oa_annotation["resource"][index]
                break
        anno.save()
        serialized_anno = json.loads(serialize("annotation", [anno]))
        assert isinstance(serialized_anno["resource"], list)
        assert anno.tags.count() == 1
        assert anno.motivation == UserAnnotation.TAGGING

        # Remove any remaining tags.
        for index, resource in enumerate(anno.oa_annotation["resource"]):
            if resource["@type"] == "oa:Tag":
                del anno.oa_annotation["resource"][index]
        # anno.oa_annotation['resource'] = [anno.oa_annotation['resource'][0]]
        anno.save()
        serialized_anno = json.loads(serialize("annotation", [anno]))
        assert isinstance(serialized_anno["resource"], dict)
        assert isinstance(serialized_anno["motivation"], str)
        assert anno.tags.count() == 0
        assert anno.tag_list == []
        assert anno.motivation == UserAnnotation.COMMENTING

    def test_annotation_serialization_with_tags(self):
        self.create_user_annotations(1, self.user_a)
        anno = UserAnnotation.objects.all().first()
        anno.oa_annotation = json.loads(
            self.valid_mirador_annotations["tag"]["oa_annotation"]
        )
        anno.save()
        kwargs = {
            "username": self.user_a.username,
            "volume": anno.canvas.manifest.pid,
            "canvas": anno.canvas.pid,
        }
        url = reverse("user_annotations", kwargs=kwargs)
        request = self.factory.get(url)
        request.user = self.user_a
        response = self.view(
            request,
            username=self.user_a.username,
            volume=self.manifest.pid,
            canvas=self.canvas.pid,
        )
        annotation = self.load_anno(response)[0]
        assert isinstance(annotation["resource"], list)
        assert isinstance(annotation["motivation"], list)
        assert "oa:tagging" in annotation["motivation"]
        assert "oa:commenting" in annotation["motivation"]

    def test_item_none(self):
        anno = UserAnnotation()
        assert anno.item is None

    def test_parse_mirador_anno_from_string(self):
        anno = UserAnnotation(
            oa_annotation=self.valid_mirador_annotations["text"]["oa_annotation"]
        )
        anno.save()
        assert anno.content == "<p>mcoewmewom</p>"

    def test_parse_mirador_anno_when_on_is_dict(self):
        oa_annotation = json.loads(
            self.valid_mirador_annotations["tag"]["oa_annotation"]
        )
        oa_annotation["on"] = oa_annotation["on"][0]
        assert isinstance(oa_annotation["on"], dict)
        anno = UserAnnotation(oa_annotation=oa_annotation)
        anno.save()
        assert anno.content == "<p>mcoewmewom</p>"

    def test_user_annotation_count(self):
        self.create_user_annotations(3, self.user_a)
        kwargs = {"volume": self.manifest.pid, "page": self.canvas.pid}
        url = reverse("_anno_count", kwargs=kwargs)
        request = self.factory.get(url)
        request.user = self.user_a
        response = AnnotationCount.as_view()(
            request, volume=self.manifest.pid, page=self.canvas.pid
        )
        assert response.context_data["volume"] == self.manifest
        assert response.context_data["page"] == self.canvas
        assert response.context_data["user_annotation_page_count"] == 3
        assert response.context_data["user_annotation_count"] == 3

    def test_current_version_context(self):
        """It should return the current version."""
        assert readux.__version__ == current_version()["APP_VERSION"]
