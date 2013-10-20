from django import template
from django.template import Node, TemplateSyntaxError
from django.conf import settings

from ..utils import build_menu

register = template.Library()

@register.filter
def account_admin_menu(request):
    """
    Given a request object, returns a navigation menu for admin settings
    """
    NAV_MENU = {
        "100": {
            "name": "Switch User",
            "reversible": "userware_switch_on",
            "url": "",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False,
            "staff_required": True,
            "icon": "icon-group",
            'sub_menu': None,
        },
        "200": {
            "name": "Database Backend",
            "reversible": "admin:index",
            "url": "",
            "pre_login_visible": False,
            "post_login_visible": True,
            "superuser_required": False, # superuser should be set as staff as well 
            "staff_required": True,
            "icon": "icon-tasks",
            'sub_menu': None,
        },
    }

    return build_menu(request, NAV_MENU)




