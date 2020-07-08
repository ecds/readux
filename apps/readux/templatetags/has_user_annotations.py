from django import template

register = template.Library()

@register.simple_tag
def has_user_annotations(manifest, user):
    return manifest.user_annotation_count(user) > 0