from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('iiif/annotations/<uuid:pk>', views.AnnotationDetail.as_view() ),
  path('iiif/<version>/annotations/<vol>/<page>', views.AnnotationsForPage.as_view(), name='page_annotations' ),
  path('iiif/<version>/<vol>/list/<page>', views.OcrForPage.as_view() )
]