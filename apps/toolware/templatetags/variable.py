from django import template
 
register = template.Library()
 
class SetVarNode(template.Node):
 
    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value
 
    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] = value
        return u''


@register.tag
def setvar(parser, token):
    """ {% setvar <var_name> to <var_value> %} """

    try:
        setvar, var_name, to_, var_value = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('Invalid arguments for %r'  % token.split_contents()[0])

    return SetVarNode(var_name, var_value)


@register.filter()
def string2var(string):
    """
    {% with user.full_name|truncatechars:16|string2var as truncated_name %}
        {{ truncated_name|highlight:search_kw }} # need to truncated and then highlight
    {% endwith %}
    """
    return string



