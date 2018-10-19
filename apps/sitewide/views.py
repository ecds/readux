##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf import settings
from django.views.generic import TemplateView

from .utils import get_app_fqdn


class IndexPageView(TemplateView):
    """ Index - home page """

    template_name = "home.html"
