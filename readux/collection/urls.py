from django.urls import path
from .views import CollectionList

urlpatterns = [
  path('', CollectionList.as_view() )
]