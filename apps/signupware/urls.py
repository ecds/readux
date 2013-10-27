from django.conf.urls import patterns, url

from views import *

urlpatterns = patterns('',

    url(r'^$',
        SignupFormProcessView.as_view(),
        name='signupware_signup_form_process'
    ),

)

