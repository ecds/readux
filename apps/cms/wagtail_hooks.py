"""Add custom .css hook"""
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.html import format_html

from wagtail.core import hooks


# Register a custom css file for the wagtail admin.
@hooks.register("insert_global_admin_css", order=100)
def global_admin_css():
    """Add /static/css/wagtail.css."""
    return format_html('<link rel="stylesheet" href="{}">', static("css/wagtail.css"))
