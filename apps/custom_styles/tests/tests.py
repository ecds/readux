# pylint: disable = no-self-use
"""Testcases for CustomStyles"""
import pytest
from django.test import TestCase, RequestFactory
from .factories import StyleFactory
from ..context_processors import add_custom_style
from ..models import Style

pytestmark = pytest.mark.django_db # pylint: disable = invalid-name

class TestCustomStyle(TestCase):
    """Test suite for CustomStyles."""
    def test_for_active_style(self):
        """
        When an inactive style is saved as active. Any styles
        marked active should become inactive.
        Note: a default style is created by the migration.
        """
        style = Style.objects.all().first()
        other_style = StyleFactory.create()
        assert style.active
        assert other_style.active is False
        other_style.active = True
        other_style.save()
        style.refresh_from_db()
        other_style.refresh_from_db()
        assert style.active is False
        assert other_style.active

    def test_create_style_with_no_styles_existing(self):
        """
        If no style is saved in the database. The first new one
        will be marked as active.
        """
        for style in Style.objects.all():
            style.delete()
        style = StyleFactory.create()
        other_style = StyleFactory.create()
        assert style.active
        assert other_style.active is False

    def test_css_property(self):
        """
        The `css` property should be css based other properties.
        """
        style = Style.objects.all().first()
        assert style.css == ':root{--link-color:#950953;}'

    def test_model_string_value(self):
        """
        The str value should start with "Style - " and the objects
        id number.
        """
        style = StyleFactory.create()
        assert str(style) == 'Style - {id}'.format(id=style.id)

    def test_style_context(self):
        """
        The context processor should return a dict with one key `css`
        and the value is the `css` property of the active Style objects.
        """
        StyleFactory.create(primary_color='#00000', active=True)
        style = Style.objects.get(active=True)
        req = RequestFactory()
        context_css = add_custom_style(req)
        assert isinstance(context_css, dict)
        assert context_css['css'] == ':root{--link-color:#00000;}'
        assert style.css == context_css['css']

    def test_no_style_exists(self):
        """
        If no active style is found, the context dict's css value
        will be an empty string.
        """
        Style.objects.all().delete()
        req = RequestFactory()
        context_css = add_custom_style(req)
        assert context_css['css'] == ''

    def test_setting_style_to_active_when_no_active_style_currently_exists(self):
        Style.objects.all().delete()
        assert Style.objects.all().count() == 0
        style1 = StyleFactory.create()
        assert style1.active
        style2 = StyleFactory.create()
        assert style2.active is False
        style1.delete()
        assert Style.objects.filter(active=True).count() == 0
        assert Style.objects.all().count() == 1
        style3 = StyleFactory.create()
        assert style3.active

    def test_making_new_style_active_when_no_active_style_currently_exists(self):
        Style.objects.all().delete()
        for num in [1, 2]:
            StyleFactory.create()
        Style.objects.get(active=True).delete()
        style = StyleFactory.create()
        assert style.active
