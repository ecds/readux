import re
from django import template
from django.template import Node, TemplateSyntaxError
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def roundplus(number):
    """
    given an number, this fuction rounds the number as the following examples:
    87 -> 87, 100 -> 100+, 188 -> 100+, 999 -> 900+, 1001 -> 1000+, ...etc
    """
    num = str(number)
    if not num.isdigit():
        return num
    
    num = str(number)
    digits = len(num)
    rounded = '100+'
    
    if digits < 3: 
        rounded = num
    elif digits == 3: 
        rounded = num[0]+'00+'
    elif digits == 4:
        rounded = num[0]+'K+'
    elif digits == 5:
        rounded = num[:1]+'K+'
    else:
        rounded = '100K+'     

    return rounded

