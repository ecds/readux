from django.test import TestCase
from .factories import ManifestFactory
from ..forms import ManifestAdminForm

class TestManifestForms(TestCase):
    def test_form_with_no_canvases(self):
        manifest = ManifestFactory.create()
        manifest.canvas_set.all().delete()
        self.assertEqual(manifest.canvas_set.count(), 0)
        self.assertFalse(manifest.canvas_set.exists())
        form = ManifestAdminForm(instance=manifest)
        self.assertEqual(form.fields['start_canvas'].queryset.count(), 0)

    def test_form_with_canvases(self):
        manifest = ManifestFactory.create()
        self.assertNotEqual(manifest.canvas_set.count(), 0)
        self.assertTrue(manifest.canvas_set.exists())
        form = ManifestAdminForm(instance=manifest)
        self.assertEqual(form.fields['start_canvas'].queryset.count(), manifest.canvas_set.count())
