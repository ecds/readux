""" Test functions for the Readux export """
from django.test import TestCase
from django.template import Context
from django.test.client import RequestFactory
from apps.iiif.canvases.tests.factories import CanvasFactory
from apps.iiif.manifests.tests.factories import ManifestFactory
from apps.users.tests.factories import UserFactory
from apps.readux.tests.factories import UserAnnotationFactory
import apps.readux.templatetags.url_replace as url_replace_tag
import apps.readux.templatetags.user_annotation_count as anno_count
import apps.readux.templatetags.has_user_annotations as has_annos

class TemplateTagTests(TestCase):
    def test_url_replace_with_kwargs(self):
        request = RequestFactory().get('collections list')
        assert url_replace_tag.url_replace(Context({'request': request}), page=1) == 'page=1'

    def test_url_replace_without_kwargs(self):
        request = RequestFactory().get('collections list')
        assert url_replace_tag.url_replace(Context({'request': request})) == ''

    def test_user_annotation_count(self):
        user = UserFactory.create()
        manifest = ManifestFactory.create()

        assert anno_count.user_annotation_count(manifest, user) == 0

        for _ in range(2):
            CanvasFactory.create(manifest=manifest)

        for _ in range(13):
            UserAnnotationFactory.create(owner=user, canvas=manifest.canvas_set.all()[0])

        for _ in range(3):
            UserAnnotationFactory.create(owner=user, canvas=manifest.canvas_set.all()[1])

        assert anno_count.user_annotation_count(manifest, user) == 16

    def test_has_user_annotations(self):
        user = UserFactory.create()
        manifest = ManifestFactory.create()

        assert has_annos.has_user_annotations(manifest, user) is False

        for _ in range(2):
            CanvasFactory.create(manifest=manifest)

        for _ in range(3):
            UserAnnotationFactory.create(owner=user, canvas=manifest.canvas_set.all()[0])

        for _ in range(4):
            UserAnnotationFactory.create(owner=user, canvas=manifest.canvas_set.all()[1])

        assert has_annos.has_user_annotations(manifest, user) is True
