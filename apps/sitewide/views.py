##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###


from django.conf import settings
from django.views.generic.base import RedirectView

from .utils import get_app_fqdn


class IndexPageView(RedirectView):
    """ Redirecting to app """

    permanent = False
    url = get_app_fqdn()
