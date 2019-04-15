from django.test import TestCase
from django.conf import settings
from django.core.checks import Warning
from .views import AnnotationListCreate
from rest_framework.test import APIRequestFactory
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
import requests
import json
from os import killpg, path, setsid
import signal
import subprocess
import logging

logger = logging.getLogger(__name__)


class AnnotationTests(APITestCase):
    factory = APIRequestFactory()
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']

    valid_annotation = {
        'oa_annotation': '''{
            "on": [{
                "full": "https://digi.vatlib.it/iiif/MSS_Vat.lat.3225/canvas/p0007",
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
        }'''
    }

    def test_annotation_creation(self):
        view = AnnotationListCreate.as_view()
        request = self.factory.post('readux/annotations/',
                                    self.valid_annotation, format='json')

        response = view(request)
        response.render()
        assert response.status_code == 201

    # TODO this should fail?
    def test_get_annotations_for_page(self):
        view = AnnotationListCreate.as_view()
        request = self.factory.get(
            'readux/annotations/MSS_Vat.lat.3225/p0005', format='json')
        response = view(request)
        response.render()
        assert response.status_code == 200

    def test_validate_iiif(self):
        iiif_validator = path.abspath(path.join(
            str(settings.ROOT_DIR.path()),
            'presentation-validator',
            'iiif-presentation-validator.py')
        )
        if (not path.isfile(iiif_validator)):
            command = 'python presentation-validator/iiif-presentation-validator.py'
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, preexec_fn=setsid
            )
            killpg(process.pid, signal.SIGTERM)
        else:
            return Warning(
                'IIIF Presentation Validator not found.',
                hint='Check README',
                id='R001'
            )        
