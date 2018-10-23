##
# @license
# Copyright Neekware Inc. All Rights Reserved.
#
# Use of this source code is governed by an MIT-style license that can be
# found in the LICENSE file at http://neekware.com/license/MIT.html
###

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import include
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.views.decorators.csrf import csrf_exempt

from rest_framework.schemas import get_schema_view
import api_v1
from .views import IndexPageView


app_name = getattr(settings, 'SITE_NAME')
admin.site.site_header = '{} Admin'.format(app_name)

urlpatterns = i18n_patterns(
    url(r'^admin/', admin.site.urls),
    prefix_default_language=True
)

i18n_aware_patterns = ([
    url(r'^$', IndexPageView.as_view(), name='index_page_view'),
], 'i18n_portal')

urlpatterns += i18n_patterns(
    url(r'^', include(i18n_aware_patterns, namespace='i18n_portal')),
    prefix_default_language=True
)

urlpatterns += [
    url(r'^api/v1/', include(('api_v1.urls', 'api_v1'), namespace='api_v1')),
    url(r'^', include('annotations.urls')),
    url(r'^', include('collection.urls')),
    url(r'^', include('volumes.urls'))
]

if settings.DEBUG:
    if getattr(settings, 'DEBUG_ENABLE_TOOLBAR', False):
        import debug_toolbar
        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
