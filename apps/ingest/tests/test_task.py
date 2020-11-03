""" Tests for ..tasks """
import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tests.factories import IServerFactory
from ..models import Local
from ..tasks import create_canvas_task

class CreateCanvasTaskTest(TestCase):
    """ Tests for the ..tasks.create_canvas_task """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = os.path.join(settings.APPS_DIR, 'ingest/fixtures/')

    def test_creating_canvas(self):
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
        local.create_manifest()

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

        local.manifest.refresh_from_db()
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

