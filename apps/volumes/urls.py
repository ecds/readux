from django.urls import path
from . import views
urlpatterns = [
    path('volumes/<vol>', views.VolumeView.as_view() ),
    path('volumes/<vol>/pages', views.VolumePages.as_view() ),
    path('volumes/<vol>/<page>', views.PageView.as_view() )
]