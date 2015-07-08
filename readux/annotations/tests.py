import json
from mock import Mock
import uuid
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, resolve
from django.test import TestCase
from django.test.utils import override_settings

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

    def test_visible_to(self):
        User = get_user_model()
        testuser = User.objects.create(username='tester')
        testadmin = User.objects.create(username='testsuper', is_superuser=True)

        Annotation.objects.create(user=testuser, text='foo')
        Annotation.objects.create(user=testuser, text='bar')
        Annotation.objects.create(user=testuser, text='baz')
        Annotation.objects.create(user=testadmin, text='qux')

        self.assertEqual(3, Annotation.objects.visible_to(testuser).count())
        self.assertEqual(4, Annotation.objects.visible_to(testadmin).count())


@override_settings(AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.ModelBackend',))
class AnnotationViewsTest(TestCase):
    fixtures = ['test_annotation_data.json']

    user_credentials = {
        'user': {'username': 'testuser', 'password': 'testing'},
        'superuser': {'username': 'testsuper', 'password': 'superme'}
    }

    def setUp(self):
        # annotation that belongs to testuser
        self.user_note = Annotation.objects \
            .get(user__username=self.user_credentials['user']['username'])
        # annotation that belongs to superuser
        self.superuser_note = Annotation.objects \
            .get(user__username=self.user_credentials['superuser']['username'])
        # NOTE: currently fixture only has one note for each user.
        # If that changes, use filter(...).first()

    def test_api_index(self):
        resp = self.client.get(reverse('annotation-api:index'))
        self.assertEqual('application/json', resp['Content-Type'])
        # expected fields in the output
        data = json.loads(resp.content)
        for f in ['version', 'name']:
            self.assert_(f in data)

    def test_list_annotations(self):
        notes = Annotation.objects.all()

        # anonymous user should see no notes
        resp = self.client.get(reverse('annotation-api:annotations'))
        self.assertEqual('application/json', resp['Content-Type'])
        data = json.loads(resp.content)
        self.assertEqual(0, len(data))

        # log in as a regular user
        self.client.login(**self.user_credentials['user'])
        resp = self.client.get(reverse('annotation-api:annotations'))
        data = json.loads(resp.content)
        # notes by this user should be listed
        user_notes = notes.filter(user__username='testuser')
        self.assertEqual(user_notes.count(), len(data))
        self.assertEqual(data[0]['id'], unicode(user_notes[0].id))

        # log in as superuser
        self.client.login(**self.user_credentials['superuser'])
        resp = self.client.get(reverse('annotation-api:annotations'))
        data = json.loads(resp.content)
        # all notes user should be listed
        self.assertEqual(notes.count(), len(data))
        self.assertEqual(data[0]['id'], unicode(notes[0].id))
        self.assertEqual(data[1]['id'], unicode(notes[1].id))

    def test_create_annotation(self):
        url = reverse('annotation-api:annotations')
        resp = self.client.post(url,
            data=json.dumps(AnnotationTestCase.annotation_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # not logged in - should not be allowed
        self.assertEqual(401, resp.status_code,
            'should return 401 Unauthorized on anonymous attempt to create annotation, got %s' \
            % resp.status_code)

        # log in as a regular user
        self.client.login(**self.user_credentials['user'])
        resp = self.client.post(url,
            data=json.dumps(AnnotationTestCase.annotation_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(303, resp.status_code,
            'should return 303 See Other on succesful annotation creation, got %s' \
            % resp.status_code)
        # get view information
        view = resolve(resp['Location'][len('http://testserver'):])
        self.assertEqual('annotation-api:view', '%s:%s' % (view.namespaces[0], view.url_name),
            'successful create should redirect to annotation view')

        # lookup the note and confirm values were set from request
        note = Annotation.objects.get(id=view.kwargs['id'])
        self.assertEqual(AnnotationTestCase.annotation_data['text'],
            note.text, 'annotation content should be set from request data')

    def test_get_annotation(self):
        # not logged in - should be denied
        resp = self.client.get(reverse('annotation-api:view',
            kwargs={'id': self.user_note.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # simulate ajax request to get 401, otherwise returns 302
        # with redirect to login page
        self.assertEqual(401, resp.status_code,
            'should return 401 Unauthorized on anonymous attempt to view annotation, got %s' \
            % resp.status_code)

        # log in as a regular user
        self.client.login(**self.user_credentials['user'])
        resp = self.client.get(reverse('annotation-api:view',
            kwargs={'id': self.user_note.id}))
        self.assertEqual('application/json', resp['Content-Type'])
        # check a few fields in the data
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.user_note.id), data['id'])
        self.assertEqual(self.user_note.text, data['text'])
        self.assertEqual(self.user_note.created.isoformat(), data['created'])

        # logged in but trying to view someone else's note
        resp = self.client.get(reverse('annotation-api:view',
            kwargs={'id': self.superuser_note.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(403, resp.status_code,
            'should return 403 Forbidden on attempt to view other user\'s annotation, got %s' \
            % resp.status_code)

        # log in as a superuser - can view other user's notes
        self.client.login(**self.user_credentials['superuser'])
        resp = self.client.get(reverse('annotation-api:view',
            kwargs={'id': self.user_note.id}))
        data = json.loads(resp.content)
        self.assertEqual(unicode(self.user_note.id), data['id'])

        # test 404
        resp = self.client.get(reverse('annotation-api:view', kwargs={'id': uuid.uuid4()}))
        self.assertEqual(404, resp.status_code)

    def test_update_annotation(self):
        # login/permission checking is common to get/update/delete views, but
        # just to be sure nothing breaks, duplicate those
        url = reverse('annotation-api:view', kwargs={'id': self.user_note.id})
        resp = self.client.put(url,
            data=json.dumps(AnnotationTestCase.annotation_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(401, resp.status_code,
            'should return 401 Unauthorized on anonymous attempt to update annotation, got %s' \
            % resp.status_code)

        # log in as a regular user
        self.client.login(**self.user_credentials['user'])
        resp = self.client.put(url,
            data=json.dumps(AnnotationTestCase.annotation_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(303, resp.status_code,
            'should return 303 See Other on succesful annotation update')
        # get view information
        self.assertEqual('http://testserver%s' % url, resp['Location'])
        # get a fresh copy from the db and check values
        n1 = Annotation.objects.get(id=self.user_note.id)
        self.assertEqual(AnnotationTestCase.annotation_data['text'],
            n1.text)
        self.assertEqual(AnnotationTestCase.annotation_data['quote'],
            n1.quote)
        self.assertEqual(AnnotationTestCase.annotation_data['ranges'],
            n1.extra_data['ranges'])

        # logged in but trying to edit someone else's note
        resp = self.client.put(reverse('annotation-api:view',
            kwargs={'id': self.superuser_note.id}),
            data=json.dumps(AnnotationTestCase.annotation_data),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(403, resp.status_code,
            'should return 403 Forbidden on attempt to view update user\'s annotation, got %s' \
            % resp.status_code)

        # log in as a superuser - can edit other user's notes
        self.client.login(**self.user_credentials['superuser'])
        data = {'text': 'this is a super annotation!'}
        resp = self.client.put(reverse('annotation-api:view',
            kwargs={'id': self.user_note.id}),
            data=json.dumps(data),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # note should be updated
        n1 = Annotation.objects.get(id=self.user_note.id)
        self.assertEqual(data['text'], n1.text)

        # test 404
        resp = self.client.put(reverse('annotation-api:view',
            kwargs={'id': str(uuid.uuid4())}),
            data=json.dumps(AnnotationTestCase.annotation_data),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(404, resp.status_code)


    def test_delete_annotation(self):
        # login/permission checking is common to get/update/delete views, but
        # just to be sure nothing breaks, duplicate those
        url = reverse('annotation-api:view', kwargs={'id': self.user_note.id})
        resp = self.client.delete(url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(401, resp.status_code,
            'should return 401 Unauthorized on anonymous attempt to delete annotation, got %s' \
            % resp.status_code)

        # log in as a regular user
        self.client.login(**self.user_credentials['user'])
        resp = self.client.delete(url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(204, resp.status_code,
            'should return 204 No Content on succesful annotation deletion')
        self.assertEqual('', resp.content,
            'deletion response should have no content')

        # attempt to delete other user's note
        url = reverse('annotation-api:view', kwargs={'id': self.superuser_note.id})
        resp = self.client.delete(url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(403, resp.status_code,
            'should return 403 Forbidden on attempt to delete another user\'s annotation, got %s' \
            % resp.status_code)

        # not explicitly tested: superuser can delete other user's note

    def test_search_annotations(self):
        search_url = reverse('annotation-api:search')
        notes = Annotation.objects.all()
        # search on partial text match
        resp = self.client.get(search_url, {'text': 'what a'})
        self.assertEqual('application/json', resp['Content-Type'])
        # check the data
        data = json.loads(resp.content)
        self.assertEqual(0, data['total'],
            'anonymous user should not see any search results')

        # login as regular user
        self.client.login(**self.user_credentials['user'])
        resp = self.client.get(search_url, {'text': 'what a'})
        # returned notes should automatically be filtered by user
        user_notes = notes.filter(user__username=self.user_credentials['user']['username'])
        data = json.loads(resp.content)
        self.assertEqual(user_notes.count(), data['total'])
        self.assertEqual(str(user_notes[0].id), data['rows'][0]['id'])

        # login as superuser - should see all notes
        self.client.login(**self.user_credentials['superuser'])
        # matches both fixture notes
        resp = self.client.get(search_url, {'text': 'what a'})
        data = json.loads(resp.content)
        self.assertEqual(notes.count(), data['total'])
        self.assertEqual(str(notes[0].id), data['rows'][0]['id'])
        self.assertEqual(str(notes[1].id), data['rows'][1]['id'])

        # search on uri
        resp = self.client.get(search_url, {'uri': notes[0].uri})
        data = json.loads(resp.content)
        self.assertEqual(1, data['total'])
        self.assertEqual(notes[0].uri, data['rows'][0]['uri'])

        # search by username
        resp = self.client.get(search_url, {'user': self.user_credentials['user']['username']})
        data = json.loads(resp.content)
        self.assertEqual(1, data['total'])
        self.assertEqual(unicode(user_notes[0].id), data['rows'][0]['id'])

        # limit/offset
        resp = self.client.get(search_url, {'limit': '1'})
        data = json.loads(resp.content)
        self.assertEqual(1, data['total'])

        resp = self.client.get(search_url, {'offset': '1'})
        data = json.loads(resp.content)
        self.assertEqual(notes.count() - 1, data['total'])
        # should return the *second* note first
        self.assertEqual(str(notes[1].id), data['rows'][0]['id'])

        # non-numeric pagination should be ignored
        resp = self.client.get(search_url, {'limit': 'three'})
        data = json.loads(resp.content)
        self.assertEqual(notes.count(), data['total'])
