import string
from django import template
register = template.Library()

@register.filter()
def contains(value, arg):
    """
    Usage:
    {% if link_url|contains:"http://www.youtube.com/" %}
    Stuff
    {% else %}
    Not stuff
    {% endif %}
    """

    return arg in value

@register.filter()
def str2tokens(string, delimiter):
    """
    Usage:
    {% with 'this, is a, string'|str2tokens:',' as token_list %}do something{% endwith %}
    """

    token_list = [token.strip() for token in string.split(delimiter)]
    return token_list

@register.assignment_tag()
def str2tokenstags(string, delimiter):
    """
    Usage:
    {% str2tokens 'a/b/c/d' '/' as token_list %}
    """

    token_list = [token.strip() for token in string.split(delimiter)]
    return token_list

@register.assignment_tag()
def get_python_string(*args, **kwargs):
    """
    Usage:
    {% get_python_string as pystring %}
    {% for alpha in pystring.ascii_uppercase %}{{alpha}}{% endfor %}
    """

    return string

@register.assignment_tag()
def double_quoted(keywords):
    """
    Usage:
    {% double_quoted str1 str2 as str_1_2 %}
    """

    quoted = '"{}"'.format(keywords)
    return quoted



