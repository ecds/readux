from django.conf.urls import url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy
from readux.collection import views

# as of django 1.8 use of patterns is deprecated. use plain list intead.
# https://docs.djangoproject.com/en/1.9/ref/urls/#patterns
urlpatterns = [
    # for now, collection cover browse is configured as site index
    # in main urls config
    url(r'^$', RedirectView.as_view(url=reverse_lazy('site-index')),
                                    name='browse'),
    url(r'^list/$', views.CollectionList.as_view(), name='list'),

    # view a single collection and items it contains
    url(r'^(?P<pid>[^/]+)/$', views.CollectionDetail.as_view(), name='view'),
    url(r'^(?P<pid>[^/]+)/covers/$', views.CollectionCoverDetail.as_view(),
        name='view-covers'),
]
