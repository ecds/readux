from django import template
from django.template import Node, TemplateSyntaxError
from django.conf import settings

from ..utils import build_menu
from account import account_settings_menu

register = template.Library()

@register.filter
def expert_search_menu(request):
    """
    Given a request object, returns a navigation menu for expert search
    """
    NAV_MENU = {
    }

    return build_menu(request, NAV_MENU)




