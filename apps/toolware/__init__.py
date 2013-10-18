__author__ = 'Val Neekman [neekware.com]'
__description__ = 'This application handles all common tasks. (hint: DRY)'
__version__ = '0.0.1'

import defaults

if defaults.TOOLWARE_TEMPLATE_TAGS_AUTO_LOAD:
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

