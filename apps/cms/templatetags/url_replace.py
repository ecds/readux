from urllib.parse import urlencode
from django import template
from django.utils.html import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()

    for kwarg in kwargs:
        try:
            query.pop(kwarg)
        except KeyError:
            pass

    query.update(kwargs)

    return mark_safe(query.urlencode())