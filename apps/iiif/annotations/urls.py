"""Url patterns for :class:`apps.iiif.annotations`"""
from django.urls import path
from . import views

urlpatterns = [
    path('iiif/<version>/<vol>/list/<page>', views.OcrForPage.as_view(), name='ocr')
]
