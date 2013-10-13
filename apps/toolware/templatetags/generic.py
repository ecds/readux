from django import template
register = template.Library()


@register.assignment_tag()
def sizeof(collection):
    """
    Usage:
    {% sizeof mylist as mylistsize %}
    """

    size = len(collection)
    return size


