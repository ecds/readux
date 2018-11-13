from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('', views.CollectionsList.as_view(), name='home' ),
  path('<collection>/', views.CollectionDetail.as_view(), name="collection" ),
  path('<collection>/<volume>', views.VolumeDetail.as_view(), name='volume' ),
  path('<collection>/<volume>/<page>', views.PageDetail.as_view(), name='page' ),
]