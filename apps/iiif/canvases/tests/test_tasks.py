"""Tests for apps.iiif.canvases.tasks"""
from unittest.mock import patch
from django.test import TestCase
from apps.iiif.manifests.tests.factories import ManifestFactory, ImageServerFactory
from .factories import CanvasFactory
from ..tasks import add_ocr_task


class TestAddOcrTaskReindex(TestCase):
    """add_ocr_task()'s reindex= kwarg lets a caller processing many canvases
    for the same manifest (rebuild_ocr --manifest) skip the per-canvas
    full-manifest Elasticsearch reindex and do it once after the batch."""

    def setUp(self):
        self.manifest = ManifestFactory.create(
            image_server=ImageServerFactory.create()
        )
        self.canvas = CanvasFactory.create(manifest=self.manifest)

    def test_reindex_false_skips_manifest_reindex(self):
        with patch(
            "apps.iiif.canvases.tasks.get_ocr", return_value=[{"content": "word"}]
        ), patch("apps.iiif.canvases.tasks.add_ocr_annotations"), patch(
            "apps.iiif.manifests.documents.ManifestDocument.update"
        ) as mock_update:
            add_ocr_task(self.canvas.id, reindex=False)

        assert mock_update.call_count == 0

    def test_reindex_defaults_to_true_and_triggers_manifest_reindex(self):
        with patch(
            "apps.iiif.canvases.tasks.get_ocr", return_value=[{"content": "word"}]
        ), patch("apps.iiif.canvases.tasks.add_ocr_annotations"), patch(
            "apps.iiif.manifests.documents.ManifestDocument.update"
        ) as mock_update:
            add_ocr_task(self.canvas.id)

        assert mock_update.call_count == 1
