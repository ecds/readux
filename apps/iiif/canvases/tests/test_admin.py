from apps.iiif.canvases.models import Canvas
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from ..admin import CanvasAdmin
from .factories import CanvasFactory

class TestCanvasAdmin(TestCase):
    def test_save_model(self):
        """Updates the canvas object"""
        # TODO: The real point of the custom Admin code is to add OCR.
        # I'm not sure that is the best place for it. Regardless,
        # this isn't really testing that.
        canvas = CanvasFactory.create(
            manifest=ManifestFactory.create(
                image_server=ImageServerFactory.create()
            )
        )

        self.assertNotEqual(canvas.label, 'Some New Something')
        canvas.label = 'Some New Something'

        canvas_model_admin = CanvasAdmin(model=Canvas, admin_site=AdminSite())
        canvas_model_admin.save_model(obj=canvas, request=None, form=None, change=None)

        canvas.refresh_from_db()
        self.assertEqual(canvas.label, 'Some New Something')
