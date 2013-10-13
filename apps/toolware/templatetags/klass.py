from django import template
register = template.Library()

@register.filter
def class_name(instance):
    return instance.__class__.__name__

@register.filter
def app_name(instance):
    return instance._meta.app_label

@register.filter
def model_name(instance):
    return '{0}.{1}'.format(app_name(instance), class_name(instance))



