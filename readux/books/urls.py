from django.conf.urls import url
from django.views.generic.base import RedirectView

from readux.books import views

# as of django 1.8 use of patterns is deprecated. use plain list intead.
# https://docs.djangoproject.com/en/1.9/ref/urls/#patterns
urlpatterns = [
    url(r'^$', views.VolumeSearch.as_view(), name='search'),
    url(r'^covers/$', views.VolumeCoverSearch.as_view(), name='search-covers'),
    url(r'^unapi/$', views.Unapi.as_view(), name='unapi'),
    url(r'^(?P<pid>[^/]+)/$', views.VolumeDetail.as_view(), name='volume'),
    url(r'^(?P<pid>[^/]+)/pdf/$', views.VolumePdf.as_view(), name='pdf'),
    url(r'^(?P<pid>[^/]+)/ocr/$', views.VolumeOcr.as_view(), name='ocr'),
    url(r'^(?P<pid>[^/]+)/text/$', views.VolumeText.as_view(), name='text'),
    url(r'^(?P<pid>[^/]+)/pages/$', views.VolumePageList.as_view(), name='pages'),
    url(r'^(?P<pid>[^/]+)/tei/$', views.VolumeTei.as_view(), name='tei'),
    url(r'^(?P<pid>[^/]+)/annotated-tei/$', views.VolumeTei.as_view(),
        {'mode': 'annotated'}, name='annotated-tei'),
    url(r'^(?P<pid>[^/]+)/export/$',
         views.AnnotatedVolumeExport.as_view(), name='webexport'),

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
        name='old-pageurl-redirect'),

    url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/(?P<mode>(thumbnail|mini-thumbnail|single-page|fs|info))/$',
        views.PageImage.as_view(),  name='page-image'),
    url(r'^(?P<vol_pid>[^/]+)/pages/(?P<pid>[^/]+)/(?P<mode>iiif)(?P<url>.*)$',
        views.PageImage.as_view())

]
