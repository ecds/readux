from django.conf import settings
from django.conf.urls import patterns, url

from views import *

urlpatterns = patterns('',
    url(
        r'^personal/$', 
        UserPersonalUpdateView.as_view(), 
        name='profileware_personal_update',
    ),
    url(
        r'^preferences/$', 
        UserPreferencesUpdateView.as_view(), 
        name='profileware_preferences_update',
    ),
)
