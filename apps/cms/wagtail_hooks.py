"""Add custom .css hook"""
from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks


# Register a custom css file for the wagtail admin.
@hooks.register("insert_global_admin_css", order=100)
def global_admin_css():
    """Add /static/css/wagtail_admin.css.

    Named wagtail_admin.css (not wagtail.css) to avoid confusion with the
    unrelated components/wagtail.scss, which styles rich-text embeds on the
    public-facing site rather than admin widgets.
    """
    return format_html('<link rel="stylesheet" href="{}">', static("css/wagtail_admin.css"))
