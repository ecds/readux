"""Template helper to check if a static file exists."""
from os.path import exists
from django import template
from django.contrib.staticfiles.finders import find
register = template.Library()

@register.filter
def static_file_exists(path_to_check):
    """Checks if a static file exists

    :param path_to_check: Relative path to static file.
    :type path_to_check: str
    :return: True if file exists
    :rtype: bool
    """

    # Remove leading '/' if there is one.
    if path_to_check.startswith('/'):
        path_to_check = path_to_check[1:]
    abs_path = find(path_to_check)

    if abs_path is None:
        return False

    return exists(abs_path)
