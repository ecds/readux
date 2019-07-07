from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('iiif/<version>/<pid>/manifest', views.ManifestDetail.as_view(), name="ManifestRender"),
  path('iiif/<version>/<pid>/export', views.ManifestExport.as_view(), name="ManifestExport"),
  path('iiif/<version>/<pid>/jekyllexport', views.JekyllExport.as_view(), name="JekyllExport"),
  path('col/<collection>/vol/<volume>/citation.ris', views.ManifestRis.as_view(), name='ris' ),
]