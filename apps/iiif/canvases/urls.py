from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('iiif/<manifest>/canvas', views.IIIFV2List.as_view() ),
  path('iiif/<manifest>/canvas/<pid>', views.IIIFV2Detail.as_view() ),
]