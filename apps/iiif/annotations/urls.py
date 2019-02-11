from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('iiif/annotations/<uuid:pk>', views.AnnotationDetail.as_view() ),
  path('iiif/annotations/<vol>/<page>', views.AnnotationsForPage.as_view() ),
  path('iiif/<version>/<vol>/list/<page>', views.OcrForPage.as_view() ),
  path('iiif/annotations/create', views.AnnotationListCreate.as_view() )
]