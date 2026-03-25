from django import template

register = template.Library()

@register.filter
def split_to_bullets(value, delimiter=";"):
    """
    Splits a string into individual items based on a delimiter and returns it as a list.
    Default delimiter is a semicolon (;).
    """
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]