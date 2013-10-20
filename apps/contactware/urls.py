from django.conf import settings
from django.conf.urls import url, patterns

import listeners
from views import *

urlpatterns = patterns('',

    url(
            r'^$', 
            ContactFormView.as_view(), 
            name='contact_form',
    ),

    url(
            r'sent/$', 
            ContactMessageReceivedView.as_view(), 
            name='contactware_message_sent',
    ),

)