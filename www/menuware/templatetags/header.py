from django import template
from django.template import Node, TemplateSyntaxError
from django.conf import settings

from ..utils import build_menu
from account import account_settings_menu
from search import expert_search_menu
register = template.Library()

@register.filter
def header_menu_right(request):
    """
    Given a request object, returns a navigation menu for the header (top-right menu)
    """
    NAV_MENU = {
        "104": {
            "name": "Login",
            "reversible": "userware_login",
            "url": "",
            "pre_login_visible": True,
            "post_login_visible": False,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": "",
            'sub_menu': None,
        },
        "105": {
            "name": "Signup",
            "reversible": "",
            "url": "/",
            "pre_login_visible": True,
            "post_login_visible": False,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": "",
            'sub_menu': None,
        },
        "106": {
            "name": "Account",
            "reversible": "",
            "url": "/",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": "icon-caret-down",
            'sub_menu': None,
        },
        "108": {
            "name": "Logout",
            "reversible": "userware_logout",
            "url": "",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": "",
            'sub_menu': None,
        }
    }

    return build_menu(request, NAV_MENU)


@register.filter
def header_menu_left(request):
    """
    Given a request object, returns a navigation menu for header (top-left menu)
    """
    NAV_MENU = {
    }

    return build_menu(request, NAV_MENU)



