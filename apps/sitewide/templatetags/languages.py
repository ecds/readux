##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django import template
from django.conf import settings


register = template.Library()

@register.filter
def altlang(request, lang):
    """
    Language-specific URL to a different language pages
    """
    enabled = getattr(settings, 'ENABLED_LANGUAGES', [getattr(settings, 'LANGUAGE_CODE')])
    url = request.path
    parts = url.split('/')

    if len(parts) < 2:
        return url

    if parts[1] in enabled:
        parts[1] = lang
    else:
        parts = [parts[0], lang] + parts[1:]

    url = '/'.join(parts)
    return url
