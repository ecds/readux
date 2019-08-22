from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('iiif/<manifest>/canvas', views.IIIFV2List.as_view(), name='RenderCanvasList' ),
  path('iiif/<manifest>/canvas/<pid>', views.IIIFV2Detail.as_view(), name='RenderCanvasDetail' ),
  path('iiif/<manifest>/startingcanvas/<pid>', views.StartingCanvas.as_view(), name='StartingCanvasManifest' )
]