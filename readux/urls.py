from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from feincms.module.page.sitemap import PageSitemap

from readux.annotations import views as annotation_views
from readux.books.sitemaps import VolumePdfSitemap, VolumeSitemap
from readux.collection.sitemaps import CollectionSitemap
from readux.collection.views import CollectionCoverList


admin.autodiscover()

sitemaps = {
    'collections': CollectionSitemap,
    'volume-pdfs': VolumePdfSitemap,
    'volumes': VolumeSitemap,
    'pages': PageSitemap
}

# choose favicon based on config, to indicate which site is running
if hasattr(settings, 'ENABLE_BETA_WARNING') and settings.ENABLE_BETA_WARNING:
    favicon = 'favicon-beta'
elif settings.DEBUG:
    favicon = 'favicon-dev'
else:
    favicon = 'favicon'


urlpatterns = patterns('',
    # for now, using collection browse as site index
    # url(r'^$', 'readux.collection.views.site_index', name="site-index"),
    # url(r'^$', 'readux.collection.views.browse', name="site-index"),
    url(r'^$', CollectionCoverList.as_view(), name="site-index"),

    url(r'^collections/', include('readux.collection.urls', namespace='collection')),
    url(r'^books/', include('readux.books.urls', namespace='books')),

    # index data for solr
    url(r'^indexdata/', include('eulfedora.indexdata.urls', namespace='indexdata')),

    # deep-zoom for images
    url(r'^dzi/', include('readux.dyndzi.urls', namespace='deepzoom')),

    # annotations
    url(r'^annotations/api/', include('readux.annotations.urls', namespace='annotation-api')),
    # annotatorjs doesn't handle trailing slash in api prefix url
    url(r'^annotations/api', annotation_views.AnnotationIndex.as_view(), name='annotation-api-prefix'),

     # add redirect for favicon at root of site
    (r'^favicon\.ico$', RedirectView.as_view(url='/static/img/%s.ico' % favicon, permanent=True)),

    # robots.txt and sitemaps
    url(r'^robots\.txt$',
        TemplateView.as_view(template_name='robots.txt',
        content_type='text/plain'), name='robots.txt'),
    url(r'^sitemap\.xml$', sitemap_views.index, {'sitemaps': sitemaps},
        name='sitemap-index'),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_views.sitemap, {'sitemaps': sitemaps},
        name='sitemap'),

    # django admin
    url(r'^admin/', include(admin.site.urls)),
    # django auth (NOTE: may need need all of auth, but at least need logout)
    url('^', include('django.contrib.auth.urls', namespace='auth')),
    # social auth
    url('', include('social.apps.django_app.urls', namespace='social')),
    # feincms
    url(r'', include('feincms.urls')),
)

if settings.DEV_ENV:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
