##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf.urls import include
from django.conf.urls import url

from .views import *


profiles_urls = [
    url(
        r'^create$',
        ProfileCreateAPIView.as_view(),
        name='api-profile-create',
    ),
    url(
        r'^list$',
        ProfileListAPIView.as_view(),
        name='api-profile-list',
    ),
    url(
        r'^update/(?P<pk>[0-9]+)$',
        ProfileUpdateAPIView.as_view(),
        name='api-profile-update',
    ),
    url(
        r'^retrieve$',
        ProfileRetrieveAPIView.as_view(),
        name='api-profile-retrieve',
    ),
    url(
        r'^retrieve/(?P<pk>[0-9]+)$',
        ProfileRetrieveAPIView.as_view(),
        name='api-profile-retrieve',
    ),
    url(
        r'^delete/(?P<pk>[0-9]+)$',
        ProfileDeleteAPIView.as_view(),
        name='api-profile-delete',
    ),
    url(
        r'^password/change$',
        ProfilePasswordChangeAPIView.as_view(),
        name='api-profile-password-change',
    ),
]
