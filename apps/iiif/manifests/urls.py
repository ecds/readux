"""URL patterns for manifests."""
from django.urls import path
from . import views

urlpatterns = [
    path('iiif/<version>/<pid>/manifest', views.ManifestDetail.as_view(), name="ManifestRender"),
    path('volume/<volume>/citation.ris', views.ManifestRis.as_view(), name='ris' ),
    path('iiif/v2/all-volumes-manifest', views.AllVolumesCollection.as_view(), name="AllVolumesManifest")
]
