""" Tests for local ingest """
from os.path import exists, join
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from ..models import Local

class LocalTest(TestCase):
    """ Tests for ingest.models.Local """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = join(str(settings.APPS_DIR), 'ingest/fixtures/')

    def test_bundle_upload(self):
        """ It should upload the zip files, unzip relevent files, and clean up. """
        for bundle in ['bundle.zip', 'nested_volume.zip']:
            local = Local()
            local.bundle = SimpleUploadedFile(
                name='bundle.zip',
                content=open(join(self.fixture_path, bundle), 'rb').read()
            )
            local.save()
            image_directory_path = local.image_directory
            ocr_directory_path = local.ocr_directory
            assert exists(join(local.image_directory, 'not_image.txt')) is False
            assert exists(join(local.ocr_directory, '00000008.jpg')) is False
            assert exists(join(local.image_directory, '00000008.jpg'))
            assert exists(join(local.ocr_directory, '00000008.tsv'))
            local.clean_up()
            assert exists(image_directory_path) is False
            assert exists(ocr_directory_path) is False
            assert exists(local.bundle.path) is False # pylint: disable=no-member
