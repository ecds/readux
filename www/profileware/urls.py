from django.conf import settings
from django.conf.urls.defaults import url
from django.conf.urls.defaults import patterns

import listeners # urls are called post models, db creation, this ensure superuser is created
from views import *

urlpatterns = patterns('',
    url(
        r'^personal/$', 
        UserProfileUpdateView.as_view(), 
        name='profileware_update',
    ),
)


