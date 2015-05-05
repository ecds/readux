import json
from mock import Mock
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, resolve
from django.test import TestCase

from readux.annotations import views
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

        # create from request with user specified
        user = get_user_model()(username='testuser')
        user.save()
        self.mockrequest.user = user
        note = Annotation.create_from_request(self.mockrequest)
        self.assertEqual(user, note.user)

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

        # associate note with a user
        user = get_user_model()(username='testuser')
        user.save()
        note.user = user
        info = note.info()
        self.assertEqual(user.username, info['user'])


class AnnotationViewsTest(TestCase):

    def test_root(self):
        resp = self.client.get(reverse('annotation-api:root'))
        self.assertEqual('application/json', resp['Content-Type'])
        # expected fields in the output
        data = json.loads(resp.content)
        for f in ['version', 'name']:
            self.assert_(f in data)

    def test_list_annotations(self):
        # create a couple of notes to list
        n1 = Annotation(text='some notes', extra_data=json.dumps({}))
        n1.save()
        n2 = Annotation(text='some more notes', extra_data=json.dumps({}))
        n2.save()

        resp = self.client.get(reverse('annotation-api:annotations'))
        self.assertEqual('application/json', resp['Content-Type'])
        data = json.loads(resp.content)
        # existing notes should be listed
        self.assertEqual(2, len(data))
        self.assertEqual(data[0]['id'], unicode(n1.id))
        self.assertEqual(data[0]['text'], n1.text)
        self.assertEqual(data[1]['id'], unicode(n2.id))
        self.assertEqual(data[1]['text'], n2.text)

    def test_create_annotation(self):
        resp = self.client.post(reverse('annotation-api:annotations'),
            data=json.dumps(AnnotationTestCase.annotation_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(303, resp.status_code,
            'should return 303 See Other on succesful annotation creation')
        # get view information
        view = resolve(resp['Location'][len('http://testserver'):])
        self.assertEqual(view.func, views.annotation,
            'successful create should redirect to annotation view')

        # lookup the note and confirm values were set from request
        note = Annotation.objects.get(id=view.kwargs['id'])
        self.assertEqual(AnnotationTestCase.annotation_data['text'],
            note.text, 'annotation content should be set from request data')

    def test_get_annotation(self):
        # create a test note to display
        n1 = Annotation(text='some notes', extra_data=json.dumps({}))
        n1.save()
        resp = self.client.get(reverse('annotation-api:view', kwargs={'id': n1.id}))
        self.assertEqual('application/json', resp['Content-Type'])
        # check a few fields in the data
        data = json.loads(resp.content)
        self.assertEqual(unicode(n1.id), data['id'])
        self.assertEqual(n1.text, data['text'])
        self.assertEqual(n1.created.isoformat(), data['created'])

    def test_update_annotation(self):
        # create a test note to update
        n1 = Annotation(text='some notes', extra_data=json.dumps({}))
        n1.save()
        url = reverse('annotation-api:view', kwargs={'id': n1.id})
        resp = self.client.put(url,
            data=json.dumps(AnnotationTestCase.annotation_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(303, resp.status_code,
            'should return 303 See Other on succesful annotation update')
        # get view information
        self.assertEqual('http://testserver%s' % url, resp['Location'])
        # get a fresh copy from the db and check values
        n1 = Annotation.objects.get(id=n1.id)
        self.assertEqual(AnnotationTestCase.annotation_data['text'],
            n1.text)
        self.assertEqual(AnnotationTestCase.annotation_data['quote'],
            n1.quote)
        self.assertEqual(AnnotationTestCase.annotation_data['ranges'],
            n1.extra_data['ranges'])

    def test_delete_annotation(self):
        # create a test note to delete
        n1 = Annotation(text='some notes', extra_data=json.dumps({}))
        n1.save()
        url = reverse('annotation-api:view', kwargs={'id': n1.id})
        resp = self.client.delete(url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(204, resp.status_code,
            'should return 204 No Content on succesful annotation deletion')
        self.assertEqual('', resp.content,
            'deletion response should have no content')

    def test_search_annotations(self):
        # create notes to search for
        user = get_user_model()(username='testuser')
        user.save()
        n1 = Annotation(text='some notes', extra_data=json.dumps({}),
            uri='http://example.com')
        n1.save()
        n2 = Annotation(text='some more notes', extra_data=json.dumps({}),
            user=user)
        n2.save()

        search_url = reverse('annotation-api:search')
        # search on partial text match
        resp = self.client.get(search_url, {'text': 'some'})
        self.assertEqual('application/json', resp['Content-Type'])
        # check the data
        data = json.loads(resp.content)
        self.assertEqual(2, data['total'])
        self.assertEqual(n1.text, data['rows'][0]['text'])
        self.assertEqual(n2.text, data['rows'][1]['text'])

        # search on uri
        resp = self.client.get(search_url, {'uri': n1.uri})
        data = json.loads(resp.content)
        self.assertEqual(1, data['total'])
        self.assertEqual(n1.uri, data['rows'][0]['uri'])

        # search by username
        resp = self.client.get(search_url, {'user': user.username})
        data = json.loads(resp.content)
        self.assertEqual(1, data['total'])
        self.assertEqual(unicode(n2.id), data['rows'][0]['id'])