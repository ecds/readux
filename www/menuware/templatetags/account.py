from django import template
from django.template import Node, TemplateSyntaxError
from django.conf import settings

from ..utils import build_menu

register = template.Library()

@register.filter
def account_settings_menu(request):
    """
    Given a request object, returns a navigation menu for account settings
    """
    NAV_MENU = {
        "100": {
            "name": "Profile",
            "reversible": "",
            "url": "/",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": " icon-user",
            'sub_menu': None,
        },
        "240": {
            "name": "Preferences",
            "reversible": "",
            "url": "/",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": "icon-cogs",
            'sub_menu': None,
        },
        "300": {
            "name": "Password Change",
            "reversible": "userware_password_change",
            "url": "",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": "icon-key",
            'sub_menu': None,
        },        
        "900": {
            "name": "Delete Account",
            "reversible": "userware_delete_account",
            "url": "",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": False,
            "selected": False,
            "icon": "icon-trash",
            'sub_menu': None,
        },
    }

    return build_menu(request, NAV_MENU)


