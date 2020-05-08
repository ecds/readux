"""Template loader to load Readux model Site Information for all templates."""
from django import template
from apps.readux.models import SiteInformation

register = template.Library()

@register.tag()
def load_readux_model():
    return SiteInformation.objects.all()