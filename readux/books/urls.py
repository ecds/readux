from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from readux.books import views

urlpatterns = patterns('',
    url(r'^$', views.VolumeSearch.as_view(), name='search'),
    url(r'^covers/$', views.VolumeCoverSearch.as_view(), name='search-covers'),
    url(r'^unapi/$', views.Unapi.as_view(), name='unapi'),
    url(r'^(?P<pid>[^/]+)/$', views.VolumeDetail.as_view(), name='volume'),
    url(r'^(?P<pid>[^/]+)/pdf/$', views.VolumePdf.as_view(), name='pdf'),
    url(r'^(?P<pid>[^/]+)/ocr/$', views.VolumeOcr.as_view(), name='ocr'),
    url(r'^(?P<pid>[^/]+)/text/$', views.VolumeText.as_view(), name='text'),
    url(r'^(?P<pid>[^/]+)/pages/$', views.VolumePageList.as_view(), name='pages'),

    # page views
    url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/$',
        views.PageDetail.as_view(), name='page'),
    url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/tei/$',
        views.PageTei.as_view(), name='page-tei'),
    # redirect from TEI to tei so either one can be used
    url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/TEI/$',
        RedirectView.as_view(pattern_name='books:page-tei')),
    # page-1.1 ocr view
    url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/ocr/$',
        views.PageOcr.as_view(), name='page-ocr'),
    # redirect from OCR to ocr so either one can be used
    url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/OCR/$',
        RedirectView.as_view(pattern_name='books:page-ocr')),

    # redirect view for old page urls without volume pids
    url(r'^pages/(?P<pid>[^/]+)/(?P<path>.*)$', views.PageRedirect.as_view(),
        name='old-pageurl-redirect')
)
