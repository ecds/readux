import json
from mock import Mock
from django.test import TestCase
from readux.annotations.models import Annotation


class AnnotationTestCase(TestCase):

    # test annotation data based on annotatorjs documentation
    # http://docs.annotatorjs.org/en/v1.2.x/annotation-format.html
    annotation_data = {
        "id": "39fc339cf058bd22176771b3e3187329",
        "annotator_schema_version": "v1.0",
        "created": "2011-05-24T18:52:08.036814",
        "updated": "2011-05-26T12:17:05.012544",
        "text": "A note I wrote",
        "quote": "the text that was annotated",
        "uri": "http://example.com",
        "ranges": [
            {
               "start": "/p[69]/span/span",
               "end": "/p[70]/span/span",
               "startOffset": 0,
               "endOffset": 120
           }
        ],
        # "user": "alice",
        "consumer": "annotateit",
        "tags": [ "review", "error" ],
        "permissions": {
            "read": ["group:__world__"],
            "admin": [],
            "update": [],
            "delete": []
        }
        # add sample extra annotation data
    }

    def setUp(self):
        # use mock to simulate django httprequest
        self.mockrequest = Mock()
        self.mockrequest.body = json.dumps(self.annotation_data)

    def test_create_from_request(self):
        note = Annotation.create_from_request(self.mockrequest)
        self.assertEqual(self.annotation_data['text'], note.text)
        self.assertEqual(self.annotation_data['quote'], note.quote)
        self.assertEqual(self.annotation_data['uri'], note.uri)
        self.assert_('ranges' in note.extra_data)
        self.assertEqual(self.annotation_data['ranges'][0]['start'],
            note.extra_data['ranges'][0]['start'])
        self.assert_('permissions' in note.extra_data)

    def test_update_from_request(self):
        # create test note to update
        note = Annotation(text="Here's the thing", quote="really",
            extra_data=json.dumps({'sample data': 'foobar'}))

        note.update_from_request(self.mockrequest)
        self.assertEqual(self.annotation_data['text'], note.text)
        self.assertEqual(self.annotation_data['quote'], note.quote)
        self.assertEqual(self.annotation_data['uri'], note.uri)
        self.assert_('ranges' in note.extra_data)
        self.assertEqual(self.annotation_data['ranges'][0]['start'],
            note.extra_data['ranges'][0]['start'])
        self.assert_('permissions' in note.extra_data)
        # existing sample data should still be present
        self.assertEqual('foobar', note.extra_data['sample data'])

    def test_info(self):
        note = Annotation.create_from_request(self.mockrequest)
        note.save()  # save so created/updated will get set
        info = note.info()
        fields = ['id', 'annotator_schema_version', 'created', 'updated',
            'text', 'quote', 'uri', 'user', 'ranges', 'permissions']
        # test that expected fields are present
        for f in fields:
            self.assert_(f in info)
        # test that dates are in isoformat
        self.assertEqual(info['created'], note.created.isoformat())
        self.assertEqual(info['updated'], note.updated.isoformat())

