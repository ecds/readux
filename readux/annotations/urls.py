from django.conf.urls import patterns, url

from readux.annotations import views
from readux.annotations.models import Annotation

# api urls only for now
urlpatterns = patterns('',
    url(r'^$', views.root, name='root'),
    # urls are without trailing slashes per annotatorjs api documentation
    url(r'^search$', views.search, name='search'),
    url(r'^annotations$', views.Annotations.as_view(), name='annotations'),
    url(r'^annotations/(?P<id>%s)$' % Annotation.UUID_REGEX,
        views.AnnotationView.as_view(), name='view'),

)
