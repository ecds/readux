__author__ = 'Val Neekman [neekware.com]'
__version__ = '0.0.1'
__note__ = 'This application handles all common tasks'

import defaults

if defaults.TOOLWARE_INCLUDE_TEMPLATE_TAGS:
    from django import template
    application_tags = [
        'toolware.templatetags.forms',
        'toolware.templatetags.rounder',
        'toolware.templatetags.highlight',
        'toolware.templatetags.variable',
        'toolware.templatetags.strings',
        'toolware.templatetags.klass',
        'toolware.templatetags.email',
        'toolware.templatetags.generic',
    ]
    for t in application_tags: template.add_to_builtins(t)

