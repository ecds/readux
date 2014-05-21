from django.conf.urls import patterns, url
from readux.books import views

urlpatterns = patterns('',
    url(r'^(?P<pid>[^/]+)/pdf/$', views.pdf, name='pdf'),
)
