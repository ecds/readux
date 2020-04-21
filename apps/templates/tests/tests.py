"""Test Templatetags for `apps.templates`."""
from django.test import TestCase
from apps.templates.templatetags.file_exists_check import static_file_exists

class TestTemplateTag(TestCase):
    def test_static_file_exists(self):
        assert static_file_exists('css/project.css')

    def test_static_file_exists_when_leading_slash_included(self):
        assert static_file_exists('/css/project.css')

    def test_static_file_does_not_exist(self):
        assert static_file_exists('css/foo.css') is False
