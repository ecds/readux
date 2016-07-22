from django.contrib.auth import get_user_model
from channels import Channel, Group
from channels.tests import ChannelTestCase
import json
from mock import patch, NonCallableMock

from readux.annotations.models import Annotation
from readux.books.consumers import volume_export
from readux.books.views import AnnotatedVolumeExport
from readux.books.export import GithubExportException


class VolumeExportTest(ChannelTestCase):

    def setUp(self):
        self.testuser = get_user_model().objects.create(username='tester')

        super(VolumeExportTest, self).setUp()

    def test_invalid(self):
        # create a test channel so notify messages can be retrieved
        Group(u"notify-tester").add(u'test-channel')
        # test invalid form submission
        Channel('volume-export').send({
            'formdata': {
                'pid': 'vol:1', 'annotations': 'user', 'mode': ''
            },
            'user': self.testuser
        })

        volume_export(self.get_next_message(u"volume-export", require=True))

        msg = json.loads(self.get_next_message(u'test-channel')['text'])
        # progress updates - start
        self.assertEqual('Export started', msg['message'])
        msg = json.loads(self.get_next_message(u'test-channel')['text'])
        # progress updates - github account warning
        self.assertEqual(AnnotatedVolumeExport.github_account_msg, msg['message'])
        self.assertEqual('warning', msg['type'])

        # form validation error
        msg = json.loads(self.get_next_message(u'test-channel')['text'])
        self.assert_('not valid' in msg['message'])
        self.assertEqual('error', msg['type'])
        self.assert_('form_errors' in msg)

    @patch('readux.books.consumers.s3_upload')
    @patch('readux.books.consumers.export')
    @patch('readux.books.consumers.annotate')
    @patch('readux.books.consumers.Repository')
    def test_download(self, mockrepo, mockannotate, mockexport,
                             mocks3_upload):

        # use mock to simulate volume being exported
        mockobj = NonCallableMock()
        mockobj.pid = 'vol:1'
        # use queryset of annotations for testing
        annotations = Annotation.objects.all()
        mockobj.annotations.return_value.filter.return_value = annotations

        mockrepo.return_value.get_object.return_value = mockobj

        # s3 upload returns the url where the zipfile can be downloaded
        mocks3_upload.return_value = 'http://samp.le/file/download.zip'

        Group(u"notify-tester").add(u'test-channel')

        Channel('volume-export').send({
            'formdata': {
                'pid': 'vol:1', 'annotations': 'user', 'mode': 'download',
                'page_one': '5',
            },
            'user': self.testuser
        })
        volume_export(self.get_next_message(u"volume-export", require=True))

        mockannotate.annotated_tei.assert_called_with(
            mockobj.generate_volume_tei.return_value, annotations)
        export_args, export_kwargs = mockexport.website_zip.call_args
        self.assertEqual(mockobj, export_args[0])
        self.assertEqual(mockannotate.annotated_tei.return_value,
                         export_args[1])
        # value from form should be passed through
        self.assertEqual(5, export_kwargs['page_one'])

        # expected progress updates in order
        status_updates = [
            'Export started',
            AnnotatedVolumeExport.github_account_msg,
            'Collected 0 annotations',
            'Generating volume TEI',
            'Finished generating volume TEI',
            'Annotated TEI',
            'Generated Jeyll zip file',
            'Zip file available for download'
        ]

        for expexted_msg in status_updates:
            msg = json.loads(self.get_next_message(u'test-channel')['text'])
            self.assertEqual(expexted_msg, msg['message'])

        # last message should also have download url
        self.assertTrue(msg['download'])
        self.assertEqual(mocks3_upload.return_value, msg['download_url'])

    @patch('readux.books.consumers.github')
    @patch('readux.books.consumers.export')
    @patch('readux.books.consumers.annotate')
    @patch('readux.books.consumers.Repository')
    def test_github(self, mockrepo, mockannotate, mockexport, mockgithub):
        # use mock to simulate volume being exported
        mockobj = NonCallableMock()
        mockobj.pid = 'vol:1'
        # use queryset of annotations for testing
        annotations = Annotation.objects.all()
        mockobj.annotations.return_value.filter.return_value = annotations

        mockrepo.return_value.get_object.return_value = mockobj

        # mock urls to be returned by export method
        repo_url = 'http://github.org/org/repo'
        ghpages_url = 'http://org.github.io/repo'
        mockexport.website_gitrepo.return_value = (
            repo_url, ghpages_url)

        Group(u"notify-tester").add(u'test-channel')

        form_data = {
            'pid': 'vol:1', 'annotations': 'user', 'mode': 'github',
            'page_one': '3', 'github_repo': 'foo'
        }
        Channel('volume-export').send({
            'formdata': form_data,
            'user': self.testuser
        })
        volume_export(self.get_next_message(u"volume-export", require=True))

        # insufficient github perms
        status_updates = [
            'Export started',
            AnnotatedVolumeExport.github_scope_msg,
        ]
        for expexted_msg in status_updates:
            msg = json.loads(self.get_next_message(u'test-channel')['text'])
            self.assertEqual(expexted_msg, msg['message'])

        # simulate public repo permissions
        mockgithub.GithubApi.connect_as_user.return_value \
                  .oauth_scopes.return_value = ['public_repo']

        Channel('volume-export').send({
            'formdata': form_data,
            'user': self.testuser
        })
        volume_export(self.get_next_message(u"volume-export", require=True))

        export_args, export_kwargs = mockexport.website_gitrepo.call_args
        self.assertEqual(self.testuser, export_args[0])
        self.assertEqual('foo', export_args[1])
        self.assertEqual(mockobj, export_args[2])
        self.assertEqual(mockannotate.annotated_tei.return_value,
                         export_args[3])
        self.assertEqual(3, export_kwargs['page_one'])

        status_updates = [
            'Export started',
            'Collected 0 annotations',
            'Generating volume TEI',
            'Finished generating volume TEI',
            'Annotated TEI',
            'Export to GitHub complete',
        ]

        for expexted_msg in status_updates:
            msg = json.loads(self.get_next_message(u'test-channel')['text'])
            self.assertEqual(expexted_msg, msg['message'])

        # last message should also have download url
        self.assertTrue(msg['github_export'])
        self.assertEqual(repo_url, msg['repo_url'])
        self.assertEqual(ghpages_url, msg['ghpages_url'])

        # github error
        Channel('volume-export').send({
            'formdata': form_data,
            'user': self.testuser
        })
        mockexport.GithubExportException = GithubExportException
        mockexport.website_gitrepo.side_effect = GithubExportException('Repository already exists')
        volume_export(self.get_next_message(u"volume-export", require=True))

        # the last message on the notify channel should have the error
        msg = json.loads(self.get_last_message(u'test-channel')['text'])
        self.assertEqual('Export failed: Repository already exists',
                         msg['message'])
        self.assertEqual('error', msg['type'])

    @patch('readux.books.consumers.github')
    @patch('readux.books.consumers.export')
    @patch('readux.books.consumers.annotate')
    @patch('readux.books.consumers.Repository')
    def test_github_update(self, mockrepo, mockannotate, mockexport, mockgithub):
        # use mock to simulate volume being exported
        mockobj = NonCallableMock()
        mockobj.pid = 'vol:1'
        # use queryset of annotations for testing
        annotations = Annotation.objects.all()
        mockobj.annotations.return_value.filter.return_value = annotations

        mockrepo.return_value.get_object.return_value = mockobj

        # simulate public repo permissions
        mockgithub.GithubApi.connect_as_user.return_value \
                  .oauth_scopes.return_value = ['public_repo']

        # mock url to be returned by export method
        pr_url = 'http://github.org/org/repo/pull/1'
        mockexport.update_gitrepo.return_value = pr_url

        Group(u"notify-tester").add(u'test-channel')

        form_data = {
            'pid': 'vol:1', 'annotations': 'user', 'mode': 'github_update',
            'page_one': '3', 'update_repo': 'foobar'
        }
        Channel('volume-export').send({
            'formdata': form_data,
            'user': self.testuser
        })
        volume_export(self.get_next_message(u"volume-export", require=True))

        export_args, export_kwargs = mockexport.update_gitrepo.call_args
        self.assertEqual(self.testuser, export_args[0])
        self.assertEqual('foobar', export_args[1])
        self.assertEqual(mockobj, export_args[2])
        self.assertEqual(mockannotate.annotated_tei.return_value,
                         export_args[3])
        self.assertEqual(3, export_kwargs['page_one'])

        # check the last message on the notify channel
        msg = json.loads(self.get_last_message(u'test-channel')['text'])
        self.assertEqual('GitHub jekyll site update completed',
                         msg['message'])
        self.assertTrue(msg['github_update'])
        self.assertEqual(pr_url, msg['pullrequest_url'])
        self.assertEqual(form_data['update_repo'], msg['repo_url'])

        # simulate update error
        mockexport.GithubExportException = GithubExportException
        mockexport.update_gitrepo.side_effect = GithubExportException('Something went wrong')

        Channel('volume-export').send({
            'formdata': form_data,
            'user': self.testuser
        })
        volume_export(self.get_next_message(u"volume-export", require=True))
        msg = json.loads(self.get_last_message(u'test-channel')['text'])
        self.assertEqual('Export failed: Something went wrong',
                         msg['message'])
        self.assertEqual('error', msg['type'])


    # helper method
    def get_last_message(self, channel):
        'Get the last available message on the specified channel'
        msg = True
        # get next message until it returns none, then return the one
        # just before that
        while msg:
            last_message = msg
            msg = self.get_next_message(channel)
        return last_message

