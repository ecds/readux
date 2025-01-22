""" Root URL configuration """

from django.conf import settings
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults as default_views
from wagtail.contrib.sitemaps.views import index, sitemap
from wagtail.contrib.sitemaps.sitemap_generator import Sitemap

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls
from wagtailautocomplete.urls.admin import urlpatterns as autocomplete_admin_urls

from apps.readux.views import ManifestsSitemap, CollectionsSitemap

sitemaps = {
    "readux-collections": CollectionsSitemap,
    "readux-volumes": ManifestsSitemap,
    "pages": Sitemap,
}

urlpatterns = [
    path("sitemap.xml", index, {"sitemaps": sitemaps}),
    path(
        "sitemap-<section>.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    re_path(r"^cms/autocomplete/", include(autocomplete_admin_urls)),
    re_path(r"^cms/", include(wagtailadmin_urls)),
    re_path(r"^documents/", include(wagtaildocs_urls)),
    re_path(r"^pages/", include(wagtail_urls)),
    re_path(r"^", include("apps.iiif.canvases.urls")),
    re_path(r"^", include("apps.iiif.manifests.urls")),
    re_path(r"^", include("apps.iiif.annotations.urls")),
    re_path(r"^", include("apps.iiif.kollections.urls")),
    re_path(r"^", include("apps.export.urls")),
    path(
        "accounts/", include("allauth.urls")
    ),  # re_path(r'^', include('readux.collection.urls')),
    # re_path(r'^', include('readux.volumes.urls')),
    # path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    # path(
    #     'about/',
    #     TemplateView.as_view(template_name=str(settings.APPS_DIR.path('templates/pages/about.html'))),
    #     name="about",
    # ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/",
        include("apps.users.urls", namespace="users"),
    ),
    # path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    re_path(r"^", include("apps.ocr.urls")),
    re_path(r"^", include("apps.readux.urls")),
    re_path(r"", include(wagtail_urls)),
    re_path(r"^summernote/", include("django_summernote.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
