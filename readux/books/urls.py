from django.conf.urls import patterns, url
from readux.books import views

urlpatterns = patterns('',
    url(r'^$', views.search, name='search'),
    url(r'^(?P<pid>[^/]+)/pdf/$', views.pdf, name='pdf'),
    url(r'^(?P<pid>[^/]+)/text/$', views.text, name='text'),
    url(r'^unapi/$', views.unapi, name='unapi'),
    # NOTE: would be nice to put pages under volume pid, but makes it hard to generate
    # target url when minting ark for ingest..
    # url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/$', views.view_page, name='page'),
    url(r'^pages/(?P<pid>[^/]+)/$', views.view_page, name='page'),
    url(r'^pages/(?P<pid>[^/]+)/thumbnail/$', views.page_image, {'mode': 'thumbnail'},
        name='page-thumbnail'),
)
