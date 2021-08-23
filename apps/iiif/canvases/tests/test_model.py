from apps.iiif.canvases.models import Canvas
from os.path import join
from django.test import TestCase
from boto3 import client, resource
from botocore.exceptions import ClientError
from moto import mock_s3
from django.conf import settings
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from .factories import CanvasFactory

class TestCanvasModels(TestCase):
    @mock_s3
    def test_delete_canvas_from_s3(self):
        """When deleted, it should delete the S3 objects"""
        conn = resource('s3', region_name='us-east-1')
        conn.create_bucket(Bucket='eagles')
        image_server = ImageServerFactory.create(storage_service='s3', storage_path='eagles')
        manifest = ManifestFactory.create(image_server=image_server)
        canvas = CanvasFactory.create(
            manifest=manifest,
            pid=f'{manifest.pid}_00000002.jpg',
            ocr_file_path=f'https://{image_server.storage_path}.s3.amazonaws.com/{manifest.pid}/_*ocr_*/00000002.tsv'
        )
        with open(join(settings.APPS_DIR, 'iiif/canvases/fixtures/00000002.jpg'), 'rb') as image_file:
            client('s3').upload_fileobj(
                image_file,
                Bucket=image_server.storage_path,
                Key=f'{canvas.manifest.pid}/00000002.jpg'
            )
        with open(join(settings.APPS_DIR, 'iiif/canvases/fixtures/00000002.tsv'), 'rb') as image_file:
            client('s3').upload_fileobj(
                image_file,
                Bucket=image_server.storage_path,
                Key=f'{canvas.manifest.pid}/_*ocr*_/00000002.tsv'
            )
        self.assertEqual(f'{canvas.manifest.pid}/00000002.jpg', canvas.file_name)
        s3_image_obj = resource('s3').Object(image_server.storage_path, canvas.file_name)
        s3_ocr_obj = resource('s3').Object(image_server.storage_path, f'{canvas.manifest.pid}/_*ocr*_/00000002.tsv')
        self.assertEqual(s3_image_obj.get()['ResponseMetadata']['HTTPHeaders']['etag'], s3_image_obj.e_tag)
        self.assertEqual(s3_ocr_obj.get()['ResponseMetadata']['HTTPHeaders']['etag'], s3_ocr_obj.e_tag)

        canvas.delete()

        get_image_error = None
        get_ocr_error = None

        try:
            s3_image_obj.get()
        except ClientError as error:
            get_image_error = error.response['Error']['Code']
        try:
            s3_ocr_obj.get()
        except ClientError as error:
            get_ocr_error = error.response['Error']['Code']

        self.assertEqual(get_image_error, 'NoSuchKey')
        self.assertEqual(get_ocr_error, 'NoSuchKey')

