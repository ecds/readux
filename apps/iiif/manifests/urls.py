from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('iiif/<version>/<pid>/plain', views.PlainExport.as_view(), name="PlainExport"),
  path('iiif/<version>/<pid>/manifest', views.ManifestDetail.as_view(), name="ManifestRender"),
  path('iiif/<version>/<pid>/export', views.ManifestExport.as_view(), name="ManifestExport"),
  path('iiif/<version>/<pid>/jekyllexport', views.JekyllExport.as_view(), name="JekyllExport"),
  path('volume/<volume>/citation.ris', views.ManifestRis.as_view(), name='ris' )
]
