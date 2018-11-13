from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Volume, Page

# def index(request):
class VolumeView(TemplateView):
    model = Volume

class VolumePages(TemplateView):
    model = Volume

class PageView(TemplateView):
    model = Volume
