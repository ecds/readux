import copy
import operator
from django import template
from django import forms
from django.utils.datastructures import SortedDict

register = template.Library()


class FieldSetNode(template.Node):
    """ Returns a subset of given form """

    def __init__(self, opcode, fields, orig_form, new_form):
        self.opcode = opcode
        self.fields = fields
        self.orig_form = orig_form
        self.new_form = new_form

    def render(self, context):
        oform = template.Variable(self.orig_form).resolve(context)
        nform = copy.copy(oform)
        if "fields" in self.opcode:
            nform.fields = SortedDict([(key, oform.fields[key]) for key in oform.fields if key in self.fields])
        if "exclude" in self.opcode:
            nform.fields = SortedDict([(key, oform.fields[key]) for key in oform.fields if key not in self.fields])
        context[self.new_form] = nform
        return u''

@register.tag
def trim_form(parser, token):
    """ 
        Returns a form that only contains a subset of the original fields (opcode: incude/exclude fields)
        Exampel: 
            <fieldset>
                <legend>Business Info</legend>
                <ul>
                {% trim_form orig_form fields biz_name,biz_city,biz_email,biz_phone as new_form %}
                {{ new_form.as_ul }}
                </ul>
            </fieldset>
            OR:
            <fieldset>
                <legend>Business Info</legend>
                <ul>
                {% trim_form orig_form exclude biz_country,biz_url as new_form %}
                {{ new_form.as_ul }}
                </ul>
            </fieldset>
    """
    try:
        trim_form, orig_form, opcode, fields, as_, new_form = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('Invalid arguments for %r'  % token.split_contents()[0])

    return FieldSetNode(opcode, fields.split(','), orig_form, new_form)



