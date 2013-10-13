from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.decorators.cache import cache_page
from django.contrib.sitemaps import views as sitemap_views
from django.contrib.sitemaps import FlatPageSitemap, GenericSitemap
from django.conf import settings

from views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Basics
urlpatterns = patterns('',
    # Home
    url(r'^$', HomeView.as_view(), name='home_page'),
    
    # Admin
    url(r'^a/admin/', include(admin.site.urls)),
)

# Specific flatpages urls
urlpatterns += patterns('django.contrib.flatpages.views',
    url(r'^site/about/$', 'flatpage', {'url': '/site/about/'}, name='about_us'),
    url(r'^site/privacy/$', 'flatpage', {'url': '/site/privacy/'}, name='privacy_policy'),
    url(r'^site/terms/$', 'flatpage', {'url': '/site/terms/'}, name='terms_of_service'),
    url(r'^site/how-it-works/$', 'flatpage', {'url': '/site/how-it-works/'}, name='how_it_works'),
)

# Plain Text Views
urlpatterns += patterns('',
    url(r'^robots\.txt$', PlainTextView.as_view(template_name='site/robots.txt')),
    url(r'^crossdomain\.xml$', PlainTextView.as_view(template_name='site/crossdomain.xml')),
)

# Error handlers
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site/403/$', 'django.views.defaults.permission_denied'),
        (r'^site/404/$', 'django.views.defaults.page_not_found'),
        (r'^site/500/$', 'django.views.defaults.server_error'),
    )


