"""URL patterns for manifests."""
from django.urls import path
from . import views

urlpatterns = [
    path('iiif/<version>/<pid>/plain', views.PlainExport.as_view(), name="PlainExport"),
    path('iiif/<version>/<pid>/export', views.ManifestExport.as_view(), name="ManifestExport"),
    path('iiif/<version>/<pid>/jekyllexport', views.JekyllExport.as_view(), name="JekyllExport"),
]
