from django.test import TestCase, Client
from django.test import RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.iiif.manifests.models import Manifest
from apps.iiif.manifests.views import ManifestExport, JekyllExport
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.export import IiifManifestExport, JekyllSiteExport, GithubExportException
from apps.iiif.manifests.github import GithubApi
from apps.users.tests.factories import UserFactory, SocialAccountFactory, SocialAppFactory, SocialTokenFactory
from iiif_prezi.loader import ManifestReader
import io
import json
import logging
import os
import re
import tempfile
import zipfile
import httpretty

User = get_user_model()

class ManifestExportTests(TestCase):
    fixtures = ['users.json', 'kollections.json', 'manifests.json', 'canvases.json', 'annotations.json', 'userannotation.json']

    def setUp(self):
        self.user = get_user_model().objects.get(pk=111)
        self.factory = RequestFactory()
        self.client = Client()
        self.volume = Manifest.objects.get(pk='464d82f6-6ae5-4503-9afc-8e3cdd92a3f1')
        self.start_canvas = self.volume.canvas_set.filter(is_starting_page=True).first()
        self.default_start_canvas = self.volume.canvas_set.filter(is_starting_page=False).first()
        self.assumed_label = ' Descrizione del Palazzo Apostolico Vaticano '
        self.assumed_pid = 'readux:st7r6'
        self.manifest_export_view = ManifestExport.as_view()
        self.jekyll_export_view = JekyllExport.as_view()
        self.sa_app = SocialAppFactory.create(
            provider='github',
            name='GitHub'
        )
        self.sa_acct = SocialAccountFactory.create(
            provider='github',
            user_id=self.user.pk,
            extra_data={'login': self.user.username}
        )
        self.sa_token = SocialTokenFactory.create(
            app_id = self.sa_app.pk,
            account_id = self.sa_acct.pk
        )
        self.jse = JekyllSiteExport(self.volume, 'v2')
        self.jse.user = self.user
        self.jse.use_github(self.user)
        self.jse.github_repo = 'marx'
        self.jse.is_testing = True
        self.jse.owners = [self.user.id]

    def test_zip_creation(self):
        zip = IiifManifestExport.get_zip(self.volume, 'v2', owners=[self.user.id])
        assert isinstance(zip, bytes)
        # unzip the file somewhere
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export-')
        iiif_zip = zipfile.ZipFile(io.BytesIO(zip), "r")
        iiif_zip.extractall(tmpdir)
        manifest_path = os.path.join(tmpdir, 'manifest.json')
        with open(manifest_path) as json_file:
            manifest = json.load(json_file)

        ocr_annotation_list_id = manifest['sequences'][0]['canvases'][0]['otherContent'][0]['@id']
        ocr_annotation_list_path = os.path.join(tmpdir, re.sub(r'\W','_', ocr_annotation_list_id) + ".json")
        assert os.path.exists(ocr_annotation_list_path) == 1

        with open(ocr_annotation_list_path) as json_file:
            ocr_annotation_list = json.load(json_file)
        assert ocr_annotation_list['@id'] == ocr_annotation_list_id

        comment_annotation_list_id = manifest['sequences'][0]['canvases'][0]['otherContent'][1]['@id']
        comment_annotation_list_path = os.path.join(tmpdir, re.sub(r'\W','_', comment_annotation_list_id) + ".json")
        assert os.path.exists(comment_annotation_list_path) == 1

        with open(comment_annotation_list_path) as json_file:
            comment_annotation_list = json.load(json_file)
        assert comment_annotation_list['@id'] == comment_annotation_list_id

    def test_jekyll_site_export(self):
        j = JekyllSiteExport(self.volume, 'v2', owners=[self.user.id])
        zip = j.get_zip()
        tempdir = j.generate_website()
        web_zip = j.website_zip()
        # j.import_iiif_jekyll(j.manifest, j.jekyll_site_dir)
        assert isinstance(zip, tempfile._TemporaryFileWrapper)
        assert "%s_annotated_site_" % (str(self.volume.pk)) in zip.name
        assert zip.name.endswith('.zip')
        assert isinstance(web_zip, tempfile._TemporaryFileWrapper)
        assert "%s_annotated_site_" % (str(self.volume.pk)) in web_zip.name
        assert web_zip.name.endswith('.zip')
        assert 'tmp-rdx-export' in tempdir
        assert tempdir.endswith('/export')
        tmpdir = tempfile.mkdtemp(prefix='tmp-rdx-export-')
        jekyll_zip = zipfile.ZipFile(zip, "r")
        jekyll_zip.extractall(tmpdir)
        jekyll_dir = os.listdir(tmpdir)[0]
        jekyll_path = os.path.join(tmpdir, jekyll_dir)
        # verify the iiif export is embedded
        iiif_path = os.path.join(jekyll_path, 'iiif_export')
        manifest_path = os.path.join(iiif_path, 'manifest.json')
        assert os.path.exists(manifest_path)
        # verify page count is correct
        assert len(os.listdir(os.path.join(jekyll_path, '_volume_pages'))) == 2
        # verify ocr annotation count is correct
        with open(os.path.join(jekyll_path, '_volume_pages', '0000.html')) as page_file:
            contents = page_file.read()
        # Depending on the order the tests are run, there might be more or less in the database.
        # TODO: Why does the database not get reset?
        assert 4 <= contents.count('ocr-line') <= 6
        # verify user annotation count is correct
        assert len(os.listdir(os.path.join(jekyll_path, '_annotations'))) == 1

    def test_get_zip_file(self):
        # Make an empty file
        dummy_file = os.path.join(tempfile.tempdir, 'file.txt')
        open(dummy_file, 'a').close()
        j = JekyllSiteExport(self.volume, 'v2', owners=[self.user.id])
        zip_file = j.get_zip_file(dummy_file)
        assert isinstance(zip_file, bytes)

    def test_manifest_export(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('ManifestExport', kwargs=kwargs)
        request = self.factory.post(url, kwargs=kwargs)
        request.user = self.user
        response = self.manifest_export_view(request, pid=self.volume.pid, version='v2')
        assert isinstance(response.getvalue(), bytes)

    def test_setting_jekyll_site_dir(self):
        self.jse

    # Things I want to test:
    # * Unzip the IIIF zip file
    #   * Verify the directory layout is correct
    #   * Open the manifest.json file
    #   * Verify that the otherContent annotation list matches the annotationlist filename
    #   * Verify that the annotationList filename matches the @id within the annotation
    # * Verify the contents of the annotationList match the OCR (or the commenting annotation)


    def test_jekyll_export_exclude_download(self):
        kwargs = { 'pid': self.volume.pid, 'version': 'v2' }
        url = reverse('JekyllExport', kwargs=kwargs)
        kwargs['deep_zoom'] = 'exclude'
        kwargs['mode'] = 'download'
        request = self.factory.post(url, data=kwargs) 
        request.user = self.user       
        response = self.jekyll_export_view(request, pid=self.volume.pid, version='v2', content_type="application/x-www-form-urlencoded")
        assert isinstance(response.getvalue(), bytes)

    def test_jekyll_export_include_download(self):
        kwargs = {'pid': self.volume.pid, 'version': 'v2'}
        url = reverse('JekyllExport', kwargs=kwargs)
        kwargs['deep_zoom'] = 'include'
        kwargs['mode'] = 'download'
        request = self.factory.post(url, data=kwargs)
        request.user = self.user
        response = self.jekyll_export_view(
            request,
            pid=self.volume.pid,
            version='v2',
            content_type='x-www-form-urlencoded'
        )
        assert isinstance(response.getvalue(), bytes)

    def test_jekyll_export_to_github(self):
        '''
        Docstring
        '''
        kwargs = {'pid': self.volume.pid, 'version': 'v2'}
        url = reverse('JekyllExport', kwargs=kwargs)
        kwargs['deep_zoom'] = 'exclude'
        kwargs['mode'] = 'github'
        request = self.factory.post(url, data=kwargs)
        request.user = self.user
        response = self.jekyll_export_view(
            request,
            pid=self.volume.pid,
            version='v2',
            content_type="application/x-www-form-urlencoded"
        )
        assert response.status_code == 200
    
    def test_use_github(self):
        assert isinstance(self.jse.github, GithubApi)
        assert self.jse.github_username == self.sa_acct.extra_data['login']
        assert self.jse.github_token == self.sa_token.token
    
    def test_github_auth_repo_given_name(self):
        auth_repo = self.jse.github_auth_repo(repo_name=self.jse.github_repo)
        assert auth_repo == "https://{t}:x-oauth-basic@github.com/{u}/{r}.git".format(t=self.sa_token.token, u=self.jse.github_username, r=self.jse.github_repo)

    def test_github_auth_repo_given_url(self):
        auth_repo = self.jse.github_auth_repo(repo_url='https://github.com/karl/{r}'.format(r=self.jse.github_repo))
        assert auth_repo == "https://{t}:x-oauth-basic@github.com/karl/{r}.git".format(t=self.sa_token.token, r=self.jse.github_repo)
    
    @httpretty.activate
    def test_github_exists(self):
        resp_body = '[{"name":"marx"}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/{u}/repos?per_page=3'.format(u=self.jse.github_username),
            body=resp_body,
            content_type="text/json"
        )

        assert self.jse.gitrepo_exists()

    @httpretty.activate
    def test_github_does_not_exist(self):
        resp_body = '[{"name":"engels"}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/{u}/repos?per_page=3'.format(u=self.jse.github_username),
            body=resp_body,
            content_type="text/json"
        )

        assert self.jse.gitrepo_exists() is False

    @httpretty.activate
    def test_create_website_gitrepo_when_repo_already_exists(self):
        # self.jse.github_repo = 'engels'
        resp_body = '[{"name":"marx"}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/{u}/repos?per_page=3'.format(u=self.jse.github_username),
            body=resp_body,
            content_type="text/json"
        )
        with self.assertRaisesMessage(GithubExportException, 'GitHub repo {r} already exists.'.format(r=self.jse.github_repo)):
            self.jse.website_gitrepo()

    @httpretty.activate
    def test_website_github_repo(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://{t}:x-oauth-basic@github.com/{u}/{r}.git/'.format(t=self.jse.github_token, u=self.jse.github_username, r=self.jse.github_repo),
            body='',
            status=200
        )
        httpretty.register_uri(httpretty.POST, 'https://api.github.com/user/repos', body='hello', status=201)
        resp_body = '[{"name":"foo"}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/{u}/repos?per_page=3'.format(u=self.jse.github_username),
            body=resp_body,
            content_type="text/json"
        )
        website = self.jse.website_gitrepo()
        assert website == ('https://github.com/{u}/{r}'.format(u=self.jse.github_username, r=self.jse.github_repo), 'https://{u}.github.io/{r}/'.format(u=self.jse.github_username, r=self.jse.github_repo))
    
    @httpretty.activate
    def test_update_githubrepo(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://{t}:x-oauth-basic@github.com/{u}/{r}.git/'.format(t=self.jse.github_token, u=self.jse.github_username, r=self.jse.github_repo),
            body='',
            status=200
        )
        pull_response_body = '{"html_url":"https://github.com/%s/%s/pull/2"}' % (self.jse.github_username, self.jse.github_repo)
        httpretty.register_uri(
            httpretty.POST,
            re.compile('https://api.github.com/.*/pulls'),
            status=201,
            body=pull_response_body
        )
        resp_body = '[{"name":"marx"}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/{u}/repos?per_page=3'.format(u=self.jse.github_username),
            body=resp_body,
            content_type="text/json"
        )
        new_pull = self.jse.update_gitrepo()
        assert new_pull == 'https://github.com/{u}/{r}/pull/2'.format(u=self.jse.github_username, r=self.jse.github_repo)

    @httpretty.activate
    def test_github_export_first_time(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://{t}:x-oauth-basic@github.com/{u}/{r}.git/'.format(t=self.jse.github_token, u=self.jse.github_username, r=self.jse.github_repo),
            body='',
            status=200
        )
        httpretty.register_uri(httpretty.POST, 'https://api.github.com/user/repos', body='hello', status=201)
        resp_body = '[{"name":"engels"}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/{u}/repos?per_page=3'.format(u=self.jse.github_username),
            body=resp_body,
            content_type="text/json"
        )
        gh_export = self.jse.github_export(self.user.email)
        assert gh_export == [
            'https://github.com/{u}/{r}'.format(u=self.jse.github_username, r=self.jse.github_repo),
            'https://{u}.github.io/{r}/'.format(u=self.jse.github_username, r=self.jse.github_repo),
            None
        ]

    @httpretty.activate
    def test_github_export_update(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://{t}:x-oauth-basic@github.com/{u}/{r}.git/'.format(t=self.jse.github_token, u=self.jse.github_username, r=self.jse.github_repo),
            body='',
            status=200
        )
        httpretty.register_uri(httpretty.POST, 'https://api.github.com/user/repos', body='hello', status=201)
        resp_body = '[{"name":"marx"}]'
        httpretty.register_uri(
            httpretty.GET,
            'https://api.github.com/users/{u}/repos?per_page=3'.format(u=self.jse.github_username),
            body=resp_body,
            content_type="text/json"
        )
        gh_export = self.jse.github_export(self.user.email)
        assert gh_export == [
            'https://github.com/{u}/{r}'.format(u=self.jse.github_username, r=self.jse.github_repo),
            'https://{u}.github.io/{r}/'.format(u=self.jse.github_username, r=self.jse.github_repo),
            'https://github.com/{u}/{r}/pull/2'.format(u=self.jse.github_username, r=self.jse.github_repo)
        ]
    
    def test_download_export(self):
        self.user.email = 'karl@marx.org'
        download = self.jse.download_export(self.user.email, self.volume)
        assert download.endswith('.zip')