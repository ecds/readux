from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.urls import reverse
# from django.core.management import call_command
import warnings
from .annotations import Annotations
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.urls import reverse
# from rest_framework.test import APIRequestFactory
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from apps.iiif.annotations.models import Annotation
from .models import UserAnnotation
import json

class AnnotationTests(TestCase):
    # factory = Client()
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
        # for fixture in fixtures:
        #     call_command('loaddata', fixture)
        # for anno in Annotation.objects.all():
        #     print(anno.pk)
        User = get_user_model()
        self.user = User.objects.create_user('zaphod', 'zaphod_beeblebrox@gmail.com', 'terrific!')
        self.user.name = 'Zaphod Beeblebrox'
        self.user.save
        self.factory = RequestFactory()
        self.client = Client()
        self.view = Annotations.as_view()


    def test_mirador_svg_annotation_creation(self):
        self.client.login(username='zaphod', password='terrific!')
        request = self.factory.post('/annotations/', data=json.dumps(self.valid_mirador_annotations['svg']), content_type="application/json")
        request.user = self.user
        response = self.view(request)
        annotation = json.loads(response.content.decode('UTF-8-sig'))
        assert annotation['annotatedBy']['name'] == 'Zaphod Beeblebrox'
        assert annotation['on']['selector']['value'] == 'xywh=535,454,681,425'
        assert response.status_code == 201


    def test_mirador_text_annotation_creation(self):
        self.client.login(username='zaphod', password='terrific!')
        request = self.factory.post('/annotations/', data=json.dumps(self.valid_mirador_annotations['text']), content_type="application/json")
        request.user = self.user
        response = self.view(request)
        annotation = json.loads(response.content.decode('UTF-8-sig'))
        assert annotation['annotatedBy']['name'] == 'Zaphod Beeblebrox'
        assert annotation['on']['selector']['value'] == 'xywh=468,2844,479,83'
        assert annotation['on']['full'] == 'https://readux-dev.org:3000/iiif/v2/readux:st7r6/canvas/fedora:emory:5622'
        assert response.status_code == 201

    def test_get_user_annotations(self):
        text_anno = UserAnnotation(
            oa_annotation=json.loads(self.valid_mirador_annotations['text']['oa_annotation']),
            owner=self.user
        )
        text_anno.save()
        self.client.login(username='zaphod', password='terrific!')
        kwargs = {'username': 'zaphod', 'volume': 'readux:st7r6', 'canvas': 'fedora:emory:5622'}
        url = reverse('annos', kwargs=kwargs)
        print(url)
        response = self.client.get(url)
        annotation = json.loads(response.content.decode('UTF-8-sig'))
        assert len(annotation) == 1
        assert response.status_code == 200
       
