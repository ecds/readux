##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf.urls import include
from django.conf.urls import url

from .views import GenericsVerifyEmailAPIView


generics_urls = [
    url(
        r'^email/exists$',
        GenericsVerifyEmailAPIView.as_view(),
        name='api-generics-email-exists',
    ),
]
