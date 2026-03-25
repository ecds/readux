"""Url patterns for :class:`apps.iiif.annotations`"""
from django.urls import path
from . import views

urlpatterns = [
    path(
        '<volume>/comments/<canvas>/ocr',
        views.WebAnnotationOCRForPage.as_view(),
        name='web_annotation_ocr'
    )
]
