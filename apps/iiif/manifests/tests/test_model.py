from apps.iiif.canvases.models import Canvas
from django.test import TestCase
from apps.iiif.canvases.models import Canvas
from apps.iiif.canvases.tests.factories import CanvasFactory
from .factories import ManifestFactory

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

