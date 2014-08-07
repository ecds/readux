from django.conf.urls import patterns, url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy
from readux.collection import views



urlpatterns = patterns('',
    # for now, collection browse is site index
    # url(r'^$', views.browse, name='browse'),
    url(r'^$', RedirectView.as_view(url=reverse_lazy('site-index')),
                                    name='browse'),

    url(r'^list/$', views.browse, {'mode': 'list'}, name='list'),

    # view a single collection and items it contains
    url(r'^(?P<pid>[^/]+)/$', views.view, name='view'),
    url(r'^(?P<pid>[^/]+)/covers/$', views.view, {'mode': 'covers'},
        name='view-covers', ),
)
