"""Tests for the rebuild_ocr management command."""
from io import StringIO
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command
from apps.users.tests.factories import UserFactory
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from apps.iiif.annotations.tests.factories import AnnotationFactory
from .factories import CanvasFactory


class TestRebuildOcrManifestReindex(TestCase):
    """rebuild_ocr --manifest processes every canvas in a manifest. Each
    canvas.save() triggers a full-manifest Elasticsearch reindex (Canvas is
    a related_model of ManifestDocument) -- for a manifest with many pages,
    reindexing once per canvas instead of once for the whole run is O(n^2)
    work."""

    def test_rebuild_manifest_reindexes_once_not_per_canvas(self):
        ocr_user = UserFactory.create(username="ocr", name="OCR")
        manifest = ManifestFactory.create(image_server=ImageServerFactory.create())
        canvases = CanvasFactory.create_batch(3, manifest=manifest)
        for canvas in canvases:
            AnnotationFactory.create(canvas=canvas, owner=ocr_user)

        fake_ocr_words = [{"content": "word", "w": 1, "h": 1, "x": 1, "y": 1}]

        with patch(
            "apps.iiif.canvases.management.commands.rebuild_ocr.services.get_ocr",
            return_value=fake_ocr_words,
        ), patch(
            "apps.iiif.manifests.documents.ManifestDocument.update"
        ) as mock_update:
            out = StringIO()
            call_command("rebuild_ocr", manifest=manifest.pid, stdout=out)

        assert "OCR rebuilt for manifest" in out.getvalue()
        assert mock_update.call_count == 1
