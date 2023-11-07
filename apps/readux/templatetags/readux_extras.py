from django.template import Library

register = Library()


@register.filter
def dict_item(dictionary, key):
    """'Template filter to allow accessing dictionary value by variable key.
    Example use::

        {{ mydict|dict_item:keyvar }}
    """
    # adapted from Princeton-CDH/geniza project https://github.com/Princeton-CDH/geniza/
    try:
        return dictionary[key]
    except AttributeError:
        # fail silently if something other than a dict is passed
        return None


@register.filter
def has_inner_hits(inner_hits):
    """Template filter to"""
    hits_dict = inner_hits.to_dict()
    for key in hits_dict.keys():
        if hits_dict[key].hits.total.value:
            return True
    return False
