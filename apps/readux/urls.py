from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  #path('', views.CollectionsList.as_view(), name='home' ),
  path('col/<collection>/', views.CollectionDetail.as_view(), name="collection" ),
  path('col/<collection>/vol/<volume>', views.VolumeDetail.as_view(), name='volume' ),
  # url for page altered to prevent conflict with Wagtail
  # TODO: find another way to resolve this conflict
  path('col/<collection>/vol/<volume>/page/<page>', views.PageDetail.as_view(), name='page' ),
  path('col/<collection>/vol/<volume>/export', views.ExportOptions.as_view(), name='export' ),
]
