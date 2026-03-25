import os
from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings
from django.core import files
from django.core.files.uploadedfile import SimpleUploadedFile
from .factories import ManifestFactory
from ..forms import ManifestAdminForm, ManifestCSVImportForm

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

    def test_bulk_metadata_form(self):
        file_path = os.path.join(
            settings.APPS_DIR,
            'iiif',
            'manifests',
            'fixtures',
            'metadata-update.csv'
        )
        with open(file_path, 'rb') as metadata_file:
            content = SimpleUploadedFile(
                name='metadata-update.csv',
                content=metadata_file.read()
            )

            csv_form = ManifestCSVImportForm(files={'csv_file': content})
            csv_form.is_valid()
            csv_form.clean()
            self.assertTrue(csv_form.is_valid())
