from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'readux.collection.views.site_index', name="site-index"),
    url(r'^collections/', include('readux.collection.urls', namespace='collection')),
    url(r'^books/', include('readux.books.urls', namespace='books')),

    # Examples:

    # url(r'^$', 'readux.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),


    # url(r'^admin/', include(admin.site.urls)),

    # index data for solr
    url(r'^indexdata/', include('eulfedora.indexdata.urls', namespace='indexdata')),
)
