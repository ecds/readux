from unittest.mock import patch
from apps.iiif.canvases.models import Canvas
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from ..admin import CanvasAdmin, resave_gethw_admin_action
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


class TestResaveGethwAdminAction(TestCase):
    """canvas.save() per canvas would trigger a full-manifest Elasticsearch
    reindex per canvas (Canvas is a related_model of ManifestDocument) --
    for several canvases selected at once in admin, that's one reindex per
    canvas instead of one for the whole batch."""

    def test_reindexes_each_manifest_once_not_per_canvas(self):
        manifest = ManifestFactory.create(image_server=ImageServerFactory.create())
        canvases = CanvasFactory.create_batch(
            3, manifest=manifest, width=0, height=0
        )
        queryset = Canvas.objects.filter(pk__in=[c.pk for c in canvases])

        with patch(
            "apps.iiif.manifests.documents.ManifestDocument.update"
        ) as mock_update:
            resave_gethw_admin_action(None, None, queryset)

        assert mock_update.call_count == 1
        for canvas in canvases:
            canvas.refresh_from_db()
            assert canvas.width == 3000
            assert canvas.height == 3000
