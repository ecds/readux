from django.conf.urls import url
from .views import AccountErrorView, GithubRepositoryList

urlpatterns = [
    url(r'^error/', AccountErrorView.as_view(), name='error'),
    url(r'^github-repos/', GithubRepositoryList.as_view(), name='github-repos'),
]