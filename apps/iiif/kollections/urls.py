"""URL patterns for Kollections"""
from django.urls import path
from . import views

urlpatterns = [
    path(
        'iiif/<version>/<pid>/collection',
        views.CollectionDetail.as_view(),
        name="CollectionRender"
    ),
    path(
        'iiif/<version>/<pid>/collection/2',
        views.ManifestsForCollection.as_view(),
        name="CollectionManifestRender"
    ),
]
