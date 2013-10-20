from django import template
from django.template import Node, TemplateSyntaxError
from django.conf import settings

from ..utils import build_menu

register = template.Library()

@register.filter
def footer_menu(request):
    """
    Given a request object, returns a navigation menu for footer (bottom of page)
    """
    NAV_MENU = {
        "100": {
            "name": "Contact Us",
            "reversible": "contact_form",
            "url": "",
            "pre_login_visible": True,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "icon": "",
            'sub_menu': None,
        },
        "200": {
            "name": "Terms of Service",
            "reversible": "terms_of_service",
            "url": "",
            "pre_login_visible": True,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "icon": "",
            'sub_menu': None,
        },
        "300": {
            "name": "Privacy Policy",
            "reversible": "privacy_policy",
            "url": "",
            "pre_login_visible": True,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "icon": "",
            'sub_menu': None,
        },
    }

    return build_menu(request, NAV_MENU)




