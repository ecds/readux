""" Tests for ..tasks """
import os
import httpretty
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.tests.factories import ImageServerFactory
    """ Tests for the ..tasks.create_canvas_task """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')
        self.image_server = ImageServerFactory(
            server_base='http://images.readux.ecds.emory',
            storage_service='s3',
            storage_path='readux'
        )

    def test_creating_manifest_form_local(self):
        """ It should create a Manifest object using uploaded metadata file. """
        local = Local(
            image_server = self.image_server
        )
        local.bundle = SimpleUploadedFile(
            name='nested_volume.zip',
            content=open(os.path.join(self.fixture_path, 'nested_volume.zip'), 'rb').read()
        )
        local.save()

        manifest = tasks.create_manifest(local)

        # Loops through the extracted metadata and compars to the corresponding
        # fields for the newly created Manifest object.
        for key in local.metadata.keys():
            assert getattr(manifest, key) == local.metadata[key]

        assert local.image_server.server_base == manifest.image_server.server_base

    @httpretty.activate
    def test_creating_manifest_form_remote(self):
        """ It should create a Manifest object using data from remote IIIF manifest. """
        with open(os.path.join(self.fixture_path, 'manifest.json')) as data:
            httpretty.register_uri(
                httpretty.GET,
                'https://archivelab.org/iiif/4757/manifest.json',
                body=data.read(),
                content_type="text/json"
            )
        remote = Remote(remote_url='https://archivelab.org/iiif/4757/manifest.json')
        manifest = tasks.create_manifest(remote)

        # Loops through the extracted metadata and compars to the corresponding
        # fields for the newly created Manifest object.
        for key in remote.metadata.keys():
            assert getattr(manifest, key) == remote.metadata[key]

        assert remote.image_server.server_base == manifest.image_server.server_base
        assert remote.remote_url == manifest.relatedlink_set.first().link

    def test_creating_canvas_form_local(self):
        """ It should create Canvas and Annotation objects for each image/OCR file in bundle. """
        local = Local(
            image_server = self.image_server
        )
        local.bundle = SimpleUploadedFile(
            name='nested_volume.zip',
            content=open(os.path.join(self.fixture_path, 'nested_volume.zip'), 'rb').read()
        )

        local.save()
        local.manifest = tasks.create_manifest(local)
        local.save()

        for key in local.metadata.keys():
            assert getattr(local.manifest, key) == local.metadata[key]

        new_canvas_task = tasks.create_canvas_task.now

        local_image_directory = local.image_directory
        local_ocr_directory = local.ocr_directory

        new_canvas_task(local.id, is_testing=True)

        local.manifest.refresh_from_db()

        assert os.path.exists(local_image_directory) is False
        assert os.path.exists(local_ocr_directory) is False

        # pylint: disable=line-too-long
        assert local.manifest.canvas_set.all().count() == 10
        assert Canvas.objects.get(pid='{m}_00000001.jpg'.format(m=local.manifest.pid)).position == 1
        assert Canvas.objects.get(pid='{m}_00000002.jpg'.format(m=local.manifest.pid)).position == 2
        assert Canvas.objects.get(pid='{m}_00000003.jpg'.format(m=local.manifest.pid)).position == 3
        assert Canvas.objects.get(pid='{m}_00000004.jpg'.format(m=local.manifest.pid)).position == 4
        assert Canvas.objects.get(pid='{m}_00000005.jpg'.format(m=local.manifest.pid)).position == 5
        assert Canvas.objects.get(pid='{m}_00000006.jpg'.format(m=local.manifest.pid)).position == 6
        assert Canvas.objects.get(pid='{m}_00000007.jpg'.format(m=local.manifest.pid)).position == 7
        assert Canvas.objects.get(pid='{m}_00000008.jpg'.format(m=local.manifest.pid)).position == 8
        assert Canvas.objects.get(pid='{m}_00000009.jpg'.format(m=local.manifest.pid)).position == 9
        assert Canvas.objects.get(pid='{m}_00000010.jpg'.format(m=local.manifest.pid)).position == 10
        assert Canvas.objects.get(pid='{m}_00000010.jpg'.format(m=local.manifest.pid)).annotation_set.all().count() == 227
        assert 'giouanile' in Canvas.objects.get(pid='{m}_00000010.jpg'.format(m=local.manifest.pid)).annotation_set.all()[17].content
        # pylint: enable=line-too-long

    @httpretty.activate
    def test_creating_canvas_form_remote(self):
        """ It should create Canvas and Annotation objects for each image/OCR file in bundle. """
        manifest_file = open(os.path.join(self.fixture_path, 'manifest.json'))
        data = manifest_file.read()
        manifest_file.close()
        httpretty.register_uri(
            httpretty.GET,
            'https://archivelab.org/iiif/4757/manifest.json',
            body=data,
            content_type="text/json"
        )
        remote = Remote(remote_url='https://archivelab.org/iiif/4757/manifest.json')
        remote.manifest = tasks.create_manifest(remote)
        remote.save()

        manifest = remote.manifest

        new_canvas_task = tasks.create_remote_canvases.now

        new_canvas_task(remote.id)
        manifest.refresh_from_db()
        assert manifest.canvas_set.count() == 6
