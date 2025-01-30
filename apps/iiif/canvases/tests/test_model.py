from apps.iiif.canvases.models import Canvas
from os.path import join
from urllib.parse import quote
from django.test import TestCase, Client
from boto3 import client, resource
from botocore.exceptions import ClientError
from moto import mock_aws
from django.conf import settings
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from .factories import CanvasFactory, CanvasNoDimensionsFactory


class TestCanvasModels(TestCase):
    fixtures = [
        "kollections.json",
        "manifests.json",
        "canvases.json",
        "annotations.json",
    ]

    def setUp(self):
        self.client = Client()
        self.canvas = Canvas.objects.get(pk="7261fae2-a24e-4a1c-9743-516f6c4ea0c9")
        self.manifest = self.canvas.manifest
        self.assumed_canvas_pid = "fedora:emory:5622"
        self.assumed_canvas_resource = "5622"
        self.assumed_volume_pid = "readux:st7r6"
        self.assumed_iiif_base = "https://loris.library.emory.edu"

    def test_properties(self):
        # httpretty.register_uri(httpretty.GET, 'https://loris.library.emory.edu')
        assert self.canvas.identifier == "%s/iiif/%s/canvas/%s" % (
            settings.HOSTNAME,
            self.assumed_volume_pid,
            self.assumed_canvas_pid,
        )
        assert self.canvas.service_id == "%s/%s" % (
            self.assumed_iiif_base,
            quote(self.assumed_canvas_pid),
        )
        assert self.canvas.anno_id == "%s/iiif/%s/annotation/%s" % (
            settings.HOSTNAME,
            self.assumed_volume_pid,
            self.assumed_canvas_pid,
        )
        assert self.canvas.thumbnail == "%s/%s/full/200,/0/default.jpg" % (
            self.assumed_iiif_base,
            self.assumed_canvas_resource,
        )
        assert self.canvas.social_media == "%s/%s/full/600,/0/default.jpg" % (
            self.assumed_iiif_base,
            self.assumed_canvas_resource,
        )
        assert self.canvas.twitter_media1 == "%s/%s/full/600,/0/default.jpg" % (
            self.assumed_iiif_base,
            self.assumed_canvas_resource,
        )
        assert self.canvas.twitter_media2 == "%s/%s/full/600,/0/default.jpg" % (
            self.assumed_iiif_base,
            self.assumed_canvas_resource,
        )
        assert self.canvas.uri == "%s/iiif/%s/" % (
            settings.HOSTNAME,
            self.assumed_volume_pid,
        )
        assert (
            self.canvas.thumbnail_crop_landscape
            == "%s/%s/full/,250/0/default.jpg"
            % (self.assumed_iiif_base, self.assumed_canvas_resource)
        )
        assert (
            self.canvas.thumbnail_crop_tallwide
            == "%s/%s/pct:5,5,90,90/,250/0/default.jpg"
            % (self.assumed_iiif_base, self.assumed_canvas_resource)
        )
        assert (
            self.canvas.thumbnail_crop_volume
            == "%s/%s/pct:15,15,70,70/,600/0/default.jpg"
            % (self.assumed_iiif_base, self.assumed_canvas_resource)
        )

    @mock_aws
    def test_delete_canvas_from_s3(self):
        """When deleted, it should delete the S3 objects"""
        conn = resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="eagles")
        image_server = ImageServerFactory.create(
            storage_service="s3", storage_path="eagles"
        )
        manifest = ManifestFactory.create(image_server=image_server)
        canvas = CanvasFactory.create(
            manifest=manifest,
            pid=f"{manifest.pid}_00000002.jpg",
            ocr_file_path=f"https://{image_server.storage_path}.s3.amazonaws.com/{manifest.pid}/_*ocr_*/00000002.tsv",
        )
        with open(
            join(settings.APPS_DIR, "iiif/canvases/fixtures/00000002.jpg"), "rb"
        ) as image_file:
            client("s3").upload_fileobj(
                image_file,
                Bucket=image_server.storage_path,
                Key=f"{canvas.manifest.pid}/00000002.jpg",
            )
        with open(
            join(settings.APPS_DIR, "iiif/canvases/fixtures/00000002.tsv"), "rb"
        ) as image_file:
            client("s3").upload_fileobj(
                image_file,
                Bucket=image_server.storage_path,
                Key=f"{canvas.manifest.pid}/_*ocr*_/00000002.tsv",
            )
        self.assertEqual(f"{canvas.manifest.pid}/00000002.jpg", canvas.file_name)
        s3_image_obj = resource("s3").Object(
            image_server.storage_path, canvas.file_name
        )
        s3_ocr_obj = resource("s3").Object(
            image_server.storage_path, f"{canvas.manifest.pid}/_*ocr*_/00000002.tsv"
        )
        self.assertEqual(
            s3_image_obj.get()["ResponseMetadata"]["HTTPHeaders"]["etag"],
            s3_image_obj.e_tag,
        )
        self.assertEqual(
            s3_ocr_obj.get()["ResponseMetadata"]["HTTPHeaders"]["etag"],
            s3_ocr_obj.e_tag,
        )

        canvas.delete()

        get_image_error = None
        get_ocr_error = None

        try:
            s3_image_obj.get()
        except ClientError as error:
            get_image_error = error.response["Error"]["Code"]
        try:
            s3_ocr_obj.get()
        except ClientError as error:
            get_ocr_error = error.response["Error"]["Code"]

        self.assertEqual(get_image_error, "NoSuchKey")
        self.assertEqual(get_ocr_error, "NoSuchKey")

    def test_no_manifest(self):
        canvas = Canvas()
        assert canvas.service_id is None
        assert canvas.resource_id is None
        assert canvas.social_media is None

    def test_string_representation(self):
        canvas = CanvasFactory.create(manifest=ManifestFactory.create())
        assert str(canvas) == canvas.pid

    def test_get_image_info(self):
        image_server = ImageServerFactory.create(server_base="http://fake.info")
        manifest = ManifestFactory.create(image_server=image_server)
        canvas = CanvasFactory.create(manifest=manifest)
        assert canvas.image_info["height"] == 3000
        assert canvas.image_info["width"] == 3000

    def test_setting_height_width_from_iiif(self):
        image_server = ImageServerFactory.create(server_base="http://fake.info")
        manifest = ManifestFactory.create(image_server=image_server)
        canvas = CanvasFactory.build()
        canvas.height = 0
        canvas.width = 0
        assert canvas.height != 3000
        assert canvas.width != 3000
        canvas.manifest = manifest
        canvas.save()
        canvas.refresh_from_db()
        assert canvas.height == 3000
        assert canvas.width == 3000

    def test_setting_height_and_width(self):
        canvas = CanvasNoDimensionsFactory.build(manifest=ManifestFactory.create())
        assert canvas.height == 0
        assert canvas.width == 0
        canvas.save()
        assert canvas.height == 3000
        assert canvas.width == 3000

    def test_setting_resource(self):
        canvas = CanvasNoDimensionsFactory.build(manifest=ManifestFactory.create())
        assert canvas.resource is None
        canvas.before_save()
        assert canvas.resource == canvas.pid
