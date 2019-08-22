from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
# from django.core.management import call_command
import warnings
from .annotations import Annotations, AnnotationCrud
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.iiif.annotations.models import Annotation
from .models import UserAnnotation
import json

class AnnotationTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']

    valid_mirador_annotations = {
        'svg': { 'oa_annotation': '''{
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
        }'''},
        'text': {
            'oa_annotation': '''{
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
            }'''
        }
    }

    def setUp(self):
        fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']
        self.User = get_user_model()
        self.user_a_uname = 'zaphod'
        self.user_a_passwd = 'terrific!'
        self.user_a = self.User.objects.create_user(self.user_a_uname, 'zaphod_beeblebrox@gmail.com', self.user_a_passwd)
        self.user_a.name = 'Zaphod Beeblebrox'
        self.user_a.save
        self.user_b_uname = 'marvin' 
        self.user_b_passwd = 'life :('
        self.user_b = self.User.objects.create_user(self.user_b_uname, 'marvin@siriuscybernetics.com', self.user_b_passwd)
        self.user_b.name = 'Marvin'
        self.user_b.save()
        self.factory = RequestFactory()
        self.client = Client()
        self.view = Annotations.as_view()
        self.crud_view = AnnotationCrud.as_view()

    def create_user_annotations(self, count, user):
        for anno in range(count):
            text_anno = UserAnnotation(
                oa_annotation=json.loads(self.valid_mirador_annotations['text']['oa_annotation']),
                owner=user
            )
            text_anno.save()
    
    def load_anno(self, response):
        return json.loads(response.content.decode('UTF-8-sig'))
    
    def rando_anno(self):
        return UserAnnotation.objects.order_by("?").first()

    def test_get_user_annotations_unauthenticated(self):
        self.create_user_annotations(5, self.user_a)
        kwargs = {'username': 'readux', 'volume': 'readux:st7r6', 'canvas': 'fedora:emory:5622'}
        url = reverse('user_annotations', kwargs=kwargs)
        response = self.client.get(url)
        assert len(UserAnnotation.objects.all()) == 5
        assert response.status_code == 200

    def test_mirador_svg_annotation_creation(self):
        self.client.login(username=self.user_a_uname, password=self.user_a_passwd)
        request = self.factory.post('/annotations-crud/', data=json.dumps(self.valid_mirador_annotations['svg']), content_type="application/json")
        request.user = self.user_a
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert annotation['annotatedBy']['name'] == 'Zaphod Beeblebrox'
        assert annotation['on']['selector']['value'] == 'xywh=535,454,681,425'
        assert response.status_code == 201


    def test_mirador_text_annotation_creation(self):
        self.client.login(username=self.user_a_uname, password=self.user_a_passwd)
        request = self.factory.post('/annotations-crud/', data=json.dumps(self.valid_mirador_annotations['text']), content_type="application/json")
        request.user = self.user_a
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert annotation['annotatedBy']['name'] == 'Zaphod Beeblebrox'
        assert annotation['on']['selector']['value'] == 'xywh=468,2844,479,83'
        assert annotation['on']['full'] == 'https://readux-dev.org:3000/iiif/v2/readux:st7r6/canvas/fedora:emory:5622'
        assert response.status_code == 201

    def test_get_user_annotations(self):
        self.create_user_annotations(4, self.user_a)
        self.client.login(username=self.user_a_uname, password=self.user_a_passwd)
        kwargs = {'username': self.user_a_uname, 'volume': 'readux:st7r6', 'canvas': 'fedora:emory:5622'}
        url = reverse('user_annotations', kwargs=kwargs)
        response = self.client.get(url)
        annotation = self.load_anno(response)
        assert len(annotation) == 4
        assert response.status_code == 200

    def test_get_only_users_user_annotations(self):
        self.create_user_annotations(5, self.user_b)
        self.create_user_annotations(4, self.user_a)
        self.client.login(username=self.user_b_uname, password=self.user_b_passwd)
        kwargs = {'username': 'marvin', 'volume': 'readux:st7r6', 'canvas': 'fedora:emory:5622'}
        url = reverse('user_annotations', kwargs=kwargs)
        response = self.client.get(url)
        annotation = self.load_anno(response)
        assert len(annotation) == 5
        assert response.status_code == 200
        assert len(UserAnnotation.objects.all()) == 9

    def test_update_user_annotation(self):
        self.create_user_annotations(1, self.user_a)
        self.client.login(username=self.user_a_uname, password=self.user_a_passwd)
        existing_anno = UserAnnotation.objects.all()[0]
        data = json.loads(self.valid_mirador_annotations['svg']['oa_annotation'])
        data['@id'] = existing_anno.id
        data = { 'oa_annotation': data }
        resource = data['oa_annotation']['resource'][0]
        resource['chars'] = 'updated annotation'
        data['oa_annotation']['resource'] = resource 
        # data = json.dumps(anno)
        data['id'] = existing_anno.id
        request = self.factory.put('/annotations-crud/', data=json.dumps(data), content_type="application/json")
        request.user = self.user_a
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert response.status_code == 201
        assert annotation['resource']['chars'] == 'updated annotation'

    def test_update_someone_elses_annotation(self):
        self.create_user_annotations(4, self.user_a)
        self.client.login(username=self.user_b_uname, password=self.user_b_passwd)
        rando_anno = self.rando_anno()
        data = { 'id': rando_anno.pk }
        request = self.factory.put('/annotations-crud/', data=json.dumps(data), content_type="application/json")
        request.user = self.user_b
        response = self.crud_view(request)
        annotation = self.load_anno(response)
        assert response.status_code == 404

    def test_updating_annotation_unauthenticated(self):
        self.create_user_annotations(1, self.user_a)
        existing_anno = UserAnnotation.objects.all()[0]
        data = json.loads(self.valid_mirador_annotations['svg']['oa_annotation'])
        data['@id'] = existing_anno.id
        data = { 'oa_annotation': data }
        resource = data['oa_annotation']['resource'][0]
        data['oa_annotation']['resource'] = resource 
        data['id'] = existing_anno.id
        request = self.factory.put('/annotations-crud/', data=json.dumps(data), content_type="application/json")
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 401
        assert message['message'] == 'You are not the owner of this annotation.'

    def test_delete_user_annotation_as_owner(self):
        self.create_user_annotations(1, self.user_a)
        self.client.login(username=self.user_a_uname, password=self.user_a_passwd)
        existing_anno = UserAnnotation.objects.all()[0]
        data = {'id': existing_anno.pk}
        request = self.factory.delete('/annotations-crud/', data=json.dumps(data), content_type="application/json")
        request.user = self.user_a
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 204
        assert len(UserAnnotation.objects.all()) == 0

    def test_delete_someone_elses_annotation(self):
        self.create_user_annotations(1, self.user_a)
        self.client.login(username=self.user_b_uname, password=self.user_b_passwd)
        rando_anno = self.rando_anno()
        data = { 'id': rando_anno.pk }
        request = self.factory.delete('/annotations-crud/', data=json.dumps(data), content_type="application/json")
        request.user = self.user_b
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 404
        assert message['message'] == 'Annotation not found.'

    def test_delete_annotation_unauthenticated(self):
        self.create_user_annotations(1, self.user_a)
        rando_anno = self.rando_anno()
        data = { 'id': rando_anno.pk }
        request = self.factory.delete('/annotations-crud/', data=json.dumps(data), content_type="application/json")
        response = self.crud_view(request)
        message = self.load_anno(response)
        assert response.status_code == 401
        assert message['message'] == 'You are not the owner of this annotation.'
