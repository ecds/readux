from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.views.generic import TemplateView

from readux.collection.sitemaps import CollectionSitemap
from readux.books.sitemaps import VolumePdfSitemap

admin.autodiscover()

sitemaps = {
    'collections': CollectionSitemap,
    'volume-pdfs': VolumePdfSitemap,
}

urlpatterns = patterns('',
    url(r'^$', 'readux.collection.views.site_index', name="site-index"),
    url(r'^collections/', include('readux.collection.urls', namespace='collection')),
    url(r'^books/', include('readux.books.urls', namespace='books')),

    # index data for solr
    url(r'^indexdata/', include('eulfedora.indexdata.urls', namespace='indexdata')),

    # robots.txt and sitemaps
    url(r'^robots\.txt$',
        TemplateView.as_view(template_name='robots.txt',
        content_type='text/plain'), name='robots.txt'),
    url(r'^sitemap\.xml$', sitemap_views.index, {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_views.sitemap, {'sitemaps': sitemaps}),

    # django admin
    url(r'^admin/', include(admin.site.urls)),
)



