from django.conf.urls import url, include
from django.urls import path# from rest_framework import routers
from readux.annotations import views

# router = routers.DefaultRouter()
# router.register(r'annotations', views.AnnotationListCreate)

urlpatterns = [
  # url(r'^', include(router.urls))
  path('readux/annotations', views.AnnotationListCreate.as_view() ),
  path('readux/annotations/<pk>', views.AnnotationUpdate.as_view() ),
  path('readux/annotations/<vol>/<page>', views.AnnotationDetail.as_view() )
]