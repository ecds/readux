from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('readux/annotations/<uuid:pk>', views.AnnotationDetail.as_view() ),
  path('readux/annotations/<vol>/<page>', views.AnnotationForPage.as_view() ),
  path('readux/annotations', views.AnnotationListCreate.as_view() )
]