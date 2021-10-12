"""
URL patterns for :class:`apps.iiif.canvases`
"""
from django.urls import path
from .views import IIIFV2Detail, IIIFV2List, CanvasResource

urlpatterns = [
    path('iiif/<manifest>/canvas', IIIFV2List.as_view(), name='RenderCanvasList'),
    path('iiif/<manifest>/canvas/<pid>', IIIFV2Detail.as_view(), name='RenderCanvasDetail'),
    path('iiif/resource/<pid>', CanvasResource.as_view(), name='ResourceResult')
]
