from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from readux.collection.sitemaps import CollectionSitemap
from readux.books.sitemaps import VolumePdfSitemap

admin.autodiscover()

sitemaps = {
    'collections': CollectionSitemap,
    'volume-pdfs': VolumePdfSitemap,
}

urlpatterns = patterns('',
    # for now, using collection browse as site index
    # url(r'^$', 'readux.collection.views.site_index', name="site-index"),
    url(r'^$', 'readux.collection.views.browse', name="site-index"),

    url(r'^collections/', include('readux.collection.urls', namespace='collection')),
    url(r'^books/', include('readux.books.urls', namespace='books')),

    # index data for solr
    url(r'^indexdata/', include('eulfedora.indexdata.urls', namespace='indexdata')),

     # add redirect for favicon at root of site
    (r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),

    # robots.txt and sitemaps
    url(r'^robots\.txt$',
        TemplateView.as_view(template_name='robots.txt',
        content_type='text/plain'), name='robots.txt'),
    url(r'^sitemap\.xml$', sitemap_views.index, {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_views.sitemap, {'sitemaps': sitemaps}),

    # django admin
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEV_ENV:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
