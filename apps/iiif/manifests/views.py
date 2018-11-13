from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.serializers import serialize
from .models import Manifest
import json

# TODO Would still be nice to use DRF. Try this?
# https://stackoverflow.com/a/35019122
class ManifestDetail(View):
    
    def get_queryset(self):
        return Manifest.objects.filter(pid=self.kwargs['pid'])
    
    def get(self, request, *args, **kwargs):
        return JsonResponse(
            json.loads(
                serialize(
                    'manifest',
                    self.get_queryset(),
                    version=kwargs['version']
                    )
                )
            )
