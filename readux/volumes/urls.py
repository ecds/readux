from django.urls import path
from . import views
urlpatterns = [
    path('volumes', views.index ),
]