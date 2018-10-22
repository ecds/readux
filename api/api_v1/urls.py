##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf.urls import include
from django.conf.urls import url

from .generics.urls import generics_urls
from .profiles.urls import profiles_urls
from . import views

urlpatterns = [
    url(r'^genetics/', include(generics_urls)),
    url(r'^profile/', include(profiles_urls)),
    url(r'^cfg', views.CfgTestView.as_view()),
    url(r'', views.api_root),
]
