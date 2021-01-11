""" Tests for ..tasks """
import os
import json
import httpretty
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tests.factories import IServerFactory
from apps.iiif.manifests.models import Manifest
from apps.ingest.models import Local, Remote
import apps.ingest.tasks as tasks

class IngestTasksTest(TestCase):
    """ Tests for the ..tasks.create_canvas_task """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')

    def test_creating_canvas_form_local(self):
        """ It should create Canvas and Annotation objects for each image/OCR file in bundle. """
        local = Local(
            image_server = IServerFactory(
                IIIF_IMAGE_SERVER_BASE='http://images.readux.ecds.emory',
                storage_service='s3',
                storage_path='readux'
            )
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

        # local_dict = local.__dict__
        # local_dict['image_directory'] = local.image_directory
        # local_dict['ocr_directory'] = local.ocr_directory

        # new_canvas_task(local_dict, is_testing=True)

        local.manifest.refresh_from_db()

        for index, image_file in enumerate(sorted(os.listdir(local.image_directory))):
            ocr_file_name = [
                f for f in os.listdir(local.ocr_directory) if f.startswith(image_file.split('.')[0])
            ][0]

            image_file_path = os.path.join(local.image_directory, image_file)

            new_canvas_task = create_canvas_task.now

            new_canvas = new_canvas_task(
                manifest_id=local.manifest.id,
                image_server_id=local.image_server.id,
                image_file_name=image_file,
                image_file_path=image_file_path,
                position=index + 1,
                ocr_file_path=os.path.join(
                    local.temp_file_path, local.ocr_directory, ocr_file_name
                ),
                is_testing=True
            )

            assert os.path.exists(new_canvas.ocr_file_path) is False
            assert os.path.exists(image_file_path) is False

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
        assert Canvas.objects.get(
                pid='{m}_00000010.jpg'.format(m=local.manifest.pid)
            ).annotation_set.all().count() == 227
        assert 'giouanile' in Canvas.objects.get(
                pid='{m}_00000010.jpg'.format(m=local.manifest.pid)
            ).annotation_set.all()[17].content
        # pylint: enable=line-too-long

    @staticmethod
    def test_cleaning_metadata():
        """ It should normalize keys and remove key/value pairs that
        do not match a Manifest field. """
        fake_metadata = {
            'pid': 'blm',
            'invalid': 'trump',
            'summary': 'idk',
            'PUBLISHER': 'ecds',
            'Published City': 'atlanta'
        }

        cleaned_metadata = tasks.clean_metadata(fake_metadata)

        manifest_fields = [f.name for f in Manifest._meta.get_fields()]

        for key in cleaned_metadata.keys():
            assert key in manifest_fields

        assert 'Published City' not in cleaned_metadata.keys()
        assert 'PUBLISHER' not in cleaned_metadata.keys()
        assert 'invalid' not in cleaned_metadata.keys()
        assert cleaned_metadata['published_city'] == fake_metadata['Published City']
        assert cleaned_metadata['publisher'] == fake_metadata['PUBLISHER']

    @httpretty.activate
    def test_metadata_from_remote_manifest(self):
        """ It should extract properties from remote IIIF manifest. """
        with open(os.path.join(self.fixture_path, 'manifest.json')) as data:
            httpretty.register_uri(
                httpretty.GET,
                'https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json',
                body=data.read(),
                content_type="text/json"
            )
            remote = Remote()
            remote.remote_url = 'https://iiif.archivelab.org/iiif/09359080.4757.emory.edu/manifest.json' # pylint: disable=line-too-long
            tasks.create_derivative_manifest(remote)
            assert remote.metadata['pid'] == '09359080.4757.emory.edu'
            assert remote.metadata['label'] == 'Address by Hon. Frederick Douglass'
            assert remote.metadata['summary'] == 'Electronic reproduction. digitized.'
            assert remote.metadata['viewingdirection'] == 'left-to-right'
            assert remote.metadata['publisher'] == 'Baltimore : Press of Thomas & Evans'
            assert remote.metadata['attribution'] == 'The Internet Archive'
            assert remote.metadata['image_server'] == 'https://iiif.archivelab.org/iiif'
            assert 'logo' not in remote.metadata
