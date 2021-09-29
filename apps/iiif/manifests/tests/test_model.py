from apps.iiif.canvases.models import Canvas
from django.test import TestCase
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tests.factories import CanvasFactory
from .factories import ManifestFactory, ImageServerFactory
from ..models import Manifest

class TestManifestModel(TestCase):
    def test_delete_manifest_and_canvases(self):
        """When deleted, it should delete all canvases"""
        # TODO: This does not really test that `Canvas.delete()` is called.
        initial_total_canvas_count = Canvas.objects.count()
        manifest = ManifestFactory.create()
        for _ in range(13):
            CanvasFactory.create(manifest=manifest)

        self.assertGreater(Canvas.objects.count(), initial_total_canvas_count)

        canvases = [canvas.id for canvas in manifest.canvas_set.all()]

        for canvas in canvases:
            self.assertTrue(Canvas.objects.filter(pk=canvas).exists())

        manifest.delete()

        for canvas in canvases:
            self.assertFalse(Canvas.objects.filter(pk=canvas).exists())
            with self.assertRaises(Canvas.DoesNotExist):
                Canvas.objects.get(pk=canvas)

        self.assertEqual(Canvas.objects.count(), initial_total_canvas_count)

    def test_user_annotation_count_no_user(self):
        """ Should return `None` when no user given. """
        manifest = ManifestFactory.create()
        assert manifest.user_annotation_count() is None

    def test_no_canvases(self):
        """ The start canvas should be `None` if no canvases. """
        manifest = Manifest()
        manifest.save()
        assert manifest.start_canvas is None
class TestImageServerModel(TestCase):
    def test_string_representation(self):
        """ It should return teh `server_base` property when cast as `str`. """
        image_server = ImageServerFactory.create()
        assert str(image_server) == image_server.server_base

    def test_bucket_is_none_when_not_s3(self):
        """ Non-S3 image servers should not have a bucket. """
        image_server = ImageServerFactory.create()
        assert image_server.bucket is None