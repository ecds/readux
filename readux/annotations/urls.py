from django.conf.urls import url

from readux.annotations import views
from readux.annotations.models import Annotation

# as of django 1.8 use of patterns is deprecated. use plain list intead.
# https://docs.djangoproject.com/en/1.9/ref/urls/#patterns

# api urls only for now
urlpatterns = [
    url(r'^$', views.AnnotationIndex.as_view(), name='index'),
    # urls are without trailing slashes per annotatorjs api documentation
    url(r'^search$', views.AnnotationSearch.as_view(), name='search'),
    url(r'^annotations$', views.Annotations.as_view(), name='annotations'),
    url(r'^annotations/(?P<id>%s)$' % Annotation.UUID_REGEX,
        views.AnnotationView.as_view(), name='view'),
]
