from django.conf.urls import patterns, url
from readux.books import views

urlpatterns = patterns('',
    url(r'^$', views.search, name='search'),
    url(r'^covers/$', views.search, {'mode': 'covers'}, name='search-covers'),
    url(r'^unapi/$', views.unapi, name='unapi'),
    url(r'^(?P<pid>[^/]+)/$', views.volume, name='volume'),
    url(r'^(?P<pid>[^/]+)/pdf/$', views.pdf, name='pdf'),
    url(r'^(?P<pid>[^/]+)/text/$', views.text, name='text'),
    url(r'^(?P<pid>[^/]+)/pages/$', views.volume_pages, name='pages'),

    # NOTE: would be nice to put individual pages under volume pid, but makes it hard to generate
    # target url when minting ark for ingest..
    # url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/$', views.view_page, name='page'),
    url(r'^pages/(?P<pid>[^/]+)/$', views.view_page, name='page'),
    url(r'^pages/(?P<pid>[^/]+)/thumbnail/$', views.page_image, {'mode': 'thumbnail'},
        name='page-thumbnail'),
    url(r'^pages/(?P<pid>[^/]+)/thumbnail/mini/$', views.page_image, {'mode': 'mini-thumbnail'},
        name='page-mini-thumb'),
    url(r'^pages/(?P<pid>[^/]+)/image/$', views.page_image, {'mode': 'single-page'},
        name='page-image'),
    url(r'^pages/(?P<pid>[^/]+)/image/fs/$', views.page_image, {'mode': 'fullsize'},
        name='page-image-fs'),
)
