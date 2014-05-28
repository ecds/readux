from django.conf.urls import patterns, url
from readux.books import views

urlpatterns = patterns('',
    url(r'^$', views.search, name='search'),
    url(r'^(?P<pid>[^/]+)/pdf/$', views.pdf, name='pdf'),
    url(r'^(?P<pid>[^/]+)/text/$', views.text, name='text'),
)
