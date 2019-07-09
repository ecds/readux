from django.conf.urls import url, include
from django.urls import path
from django.views.generic import RedirectView
from . import views
# from .views import PageRedirectView

urlpatterns = [
  #path('', views.CollectionsList.as_view(), name='home' ),
  path('col/<collection>/', views.CollectionDetail.as_view(), name="collection" ),
  path('col/<collection>/vol/<volume>', views.VolumeDetail.as_view(), name='volume' ),
  # url for page altered to prevent conflict with Wagtail
  # TODO: find another way to resolve this conflict
  path('col/<collection>/vol/<volume>/page/<page>', views.PageDetail.as_view(), name='page' ),
#   path('col/<collection>/vol/<volume>/page/', RedirectView.as_view(pattern_name='page'), name='page 1' ),
#   path('col/<collection>/vol/<volume>/page/', PageRedirectView.as_view(), name='page 1' ),
  path('col/<collection>/vol/<volume>/export', views.ExportOptions.as_view(), name='export' ),
]
