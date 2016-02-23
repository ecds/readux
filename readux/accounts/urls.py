from django.conf.urls import url
from .views import AccountErrorView

urlpatterns = [
    url(r'^error/', AccountErrorView.as_view(), name='error'),
]