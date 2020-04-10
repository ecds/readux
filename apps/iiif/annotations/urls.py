"""Url patterns for `apps.iiif.annotations`"""
from django.urls import path
from . import views

urlpatterns = [
    path(
        'iiif/<version>/annotations/<vol>/<page>',
        views.AnnotationsForPage.as_view(),
        name='page_annotations'
    ),
    path('iiif/<version>/<vol>/list/<page>', views.OcrForPage.as_view(), name='ocr')
]
