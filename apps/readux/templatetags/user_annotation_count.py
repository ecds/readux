from django import template

register = template.Library()

@register.simple_tag
def user_annotation_count(manifest, user):
    return manifest.user_annotation_count(user)