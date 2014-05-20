from django.conf.urls import patterns, url
from readux.collection import views

urlpatterns = patterns('',
    url(r'^$', views.browse, name='browse'),
    url(r'^(?P<pid>[^/]+)/$', views.view, name='view'),
)
