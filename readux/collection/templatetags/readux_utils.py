from django.template.defaulttags import register

@register.filter
def dict_item(dictionary, key):
    # template filter to allow accessing dictionary value by variable key
    return dictionary.get(key)